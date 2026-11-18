import ast
import logging

from odoo import _, fields, models
from odoo.tools import SQL

_logger = logging.getLogger(__name__)

NAVIGATION_KEYS = ("ledger_navigation_account_ids", "ledger_navigation_group_ids")


class AccountGeneralLedgerReportHandler(models.AbstractModel):
    _inherit = "account.general.ledger.report.handler"

    def _custom_options_initializer(self, report, options, previous_options):
        super()._custom_options_initializer(report, options, previous_options=previous_options)
        # Odoo restores the last options of the report from the browser
        # session when it is opened again from the menu, including the search
        # bar text, while the search bar input itself stays empty. Opened from
        # the menu, the ledger must show all accounts and the navigation must
        # start from scratch, so this hidden search and the navigation list
        # are dropped. They are kept when the ledger is opened by the
        # navigation buttons or from another report ("ledger_navigation"
        # context key), and when coming back through the breadcrumb (where
        # is_opening_report is not set).
        if (
            previous_options.get("is_opening_report")
            and not self.env.context.get("ledger_navigation")
            and "default_filter_accounts" not in self.env.context
        ):
            if options.get("filter_search_bar") or any(previous_options.get(key) for key in NAVIGATION_KEYS):
                _logger.info(
                    "Ledger navigation - general ledger opened from the menu: hidden search %r and navigation list "
                    "(accounts %s, groups %s) dropped",
                    options.get("filter_search_bar"),
                    previous_options.get("ledger_navigation_account_ids"),
                    previous_options.get("ledger_navigation_group_ids"),
                )
            options.pop("filter_search_bar", None)
        else:
            # With default_filter_accounts in the context (ledger opened from
            # another report or by the navigation), Odoo never keeps the
            # search bar text when the report is reloaded (period change...),
            # while the input still shows it: keep it, so that the buttons
            # still start from the account on screen.
            if self.env.context.get("default_filter_accounts") and previous_options.get("filter_search_bar"):
                options["filter_search_bar"] = previous_options["filter_search_bar"]
            # Kept from one ledger to the next, see action_open_adjacent_account().
            for key in NAVIGATION_KEYS:
                if previous_options.get(key) is not None:
                    options[key] = previous_options[key]
        # "replace_current_action" makes the client open the next ledger in
        # place of the current one, instead of stacking a new breadcrumb at
        # every click (see account_report_controller.esm.js).
        options["buttons"] += [
            {
                "name": _("Previous account"),
                "sequence": 200,
                "action": "action_open_adjacent_account",
                "action_param": "previous",
                "always_show": True,
                "branch_allowed": True,
                "replace_current_action": True,
            },
            {
                "name": _("Next account"),
                "sequence": 210,
                "action": "action_open_adjacent_account",
                "action_param": "next",
                "always_show": True,
                "branch_allowed": True,
                "replace_current_action": True,
            },
        ]

    def _get_navigation_accounts(self, report, options):
        """Return the accounts listed by the general ledger for these options,
        as a dict {code: account} sorted by code.

        Same scope as the ledger itself: every account with entries up to the
        end of the period, income and expense accounts being only taken from
        the start of the current fiscal year.
        """
        date_from = fields.Date.from_string(options["date"]["date_from"])
        fiscalyear_date_from = self.env.company.compute_fiscalyear_dates(date_from)["date_from"]
        query = report._get_report_query(options, "from_beginning", [
            "|",
            ("account_id.include_initial_balance", "=", True),
            ("date", ">=", fiscalyear_date_from),
        ])
        self.env.cr.execute(query.select(SQL("DISTINCT account_move_line.account_id")))
        accounts = self.env["account.account"].browse(row[0] for row in self.env.cr.fetchall())
        # The account code depends on the company: read it with one of the
        # report companies the account belongs to.
        companies = self.env["res.company"].browse(report.get_report_company_ids(options))
        accounts_by_code = {}
        for account in accounts:
            account = account.with_company((account.company_ids & companies)[:1] or account.company_ids[:1])
            if account.code:
                accounts_by_code[account.code] = account
        return dict(sorted(accounts_by_code.items()))

    def _filter_navigation_codes(self, accounts_by_code, account_ids, group_ids):
        """Return the codes of the accounts shown on screen: the account lines
        shown, and every account below an account group line matching the
        search (see getLedgerNavigationScreenList() on the client side)."""
        codes = []
        for code, account in accounts_by_code.items():
            group = account.group_id
            while group and group.id not in group_ids:
                group = group.parent_id
            if account.id in account_ids or group:
                codes.append(code)
        return codes

    def action_open_adjacent_account(self, options, direction):
        """Open the general ledger on the account before or after the current
        one, among the accounts shown on screen.

        - An account code in the search bar is the current account (this is
          how Odoo opens the ledger from the trial balance). If it was reached
          from a list filtered by a search (in the general ledger, or in the
          report it was opened from), the navigation stays within that list,
          as long as the account still belongs to it.
        - Any other search shown on screen filters the list: the navigation
          goes through the accounts it shows, and starts from its first (or
          last) account. A list of only one account makes it the current one.
        """
        report = self.env["account.report"].browse(options["report_id"])
        accounts_by_code = self._get_navigation_accounts(report, options)
        search = (options.get("filter_search_bar") or "").strip()
        visible_account_ids = options.get("ledger_navigation_visible_account_ids")
        matched_group_ids = options.get("ledger_navigation_matched_group_ids")

        current = None
        account_ids = group_ids = None
        if search in accounts_by_code:
            current = search
            account_ids = options.get("ledger_navigation_account_ids")
            group_ids = options.get("ledger_navigation_group_ids")
        elif visible_account_ids is not None:
            account_ids, group_ids = visible_account_ids, matched_group_ids or []

        codes = list(accounts_by_code)
        if account_ids is not None:
            codes = self._filter_navigation_codes(accounts_by_code, account_ids, group_ids or [])
            if current and current not in codes:
                account_ids = group_ids = None
                codes = list(accounts_by_code)
            elif not current and len(codes) == 1:
                current = codes[0]

        if current:
            index = codes.index(current) + (1 if direction == "next" else -1)
            code = codes[index] if 0 <= index < len(codes) else None
        else:
            code = (codes[:1] if direction == "next" else codes[-1:]) or [None]
            code = code[0]

        _logger.info(
            "Ledger navigation - general ledger %s: search=%r, shown on screen: accounts=%s matched groups=%s, "
            "navigation list: accounts=%s groups=%s, %s accounts in the ledger, %s in the navigation list %s, "
            "current=%r -> %r",
            direction, search, visible_account_ids, matched_group_ids, account_ids, group_ids,
            len(accounts_by_code), len(codes), codes, current, code,
        )

        if not code:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "type": "info",
                    "message": _("This is the last account.") if direction == "next" else _("This is the first account."),
                },
            }

        new_options = report.get_options(options)
        new_options["not_reset_journals_filter"] = True
        new_options["unfold_all"] = True
        new_options["filter_search_bar"] = code
        new_options["ledger_navigation_account_ids"] = account_ids
        new_options["ledger_navigation_group_ids"] = group_ids

        action = self.env["ir.actions.actions"]._for_xml_id("account_reports.action_account_report_general_ledger")
        action["params"] = {"options": new_options, "ignore_session": True}
        # The search bar input is filled from default_filter_accounts on load.
        action["context"] = dict(ast.literal_eval(action["context"]), default_filter_accounts=code, ledger_navigation=True)
        return action
