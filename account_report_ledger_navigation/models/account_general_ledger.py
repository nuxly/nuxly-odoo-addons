import ast

from odoo import _, fields, models
from odoo.tools import SQL


class AccountGeneralLedgerReportHandler(models.AbstractModel):
    _inherit = "account.general.ledger.report.handler"

    def _custom_options_initializer(self, report, options, previous_options):
        super()._custom_options_initializer(report, options, previous_options=previous_options)
        # Kept from one ledger to the next, see AccountReport.caret_option_open_general_ledger().
        if previous_options.get("ledger_navigation_search"):
            options["ledger_navigation_search"] = previous_options["ledger_navigation_search"]
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

    def _get_navigation_account_codes(self, report, options):
        """Return the codes of the accounts listed by the general ledger for
        these options, sorted.

        Same scope as the ledger itself: every account with entries up to the
        end of the period, income and expense accounts being only taken from
        the start of the current fiscal year.

        When the ledger was opened from a trial balance filtered by its search
        bar, only the accounts this search shows in the trial balance are
        kept, as long as the current account is one of them (otherwise the
        user has searched another account since, and the trial balance search
        no longer applies).
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
        codes = sorted(accounts_by_code)

        trial_balance_search = (options.get("ledger_navigation_search") or "").strip().lower()
        if trial_balance_search:
            matched_codes = [
                code for code in codes
                if self._is_account_shown_by_search(accounts_by_code[code], trial_balance_search)
            ]
            if (options.get("filter_search_bar") or "").strip() in matched_codes:
                codes = matched_codes
        return codes

    def _is_account_shown_by_search(self, account, search):
        """Whether the trial balance search bar shows this account: like on the
        client side, the account line matches when its name contains the text,
        or when one of its account group lines does (a matching line also
        shows the lines below it)."""
        names = [account.display_name]
        group = account.group_id
        while group:
            names.append(group.display_name)
            group = group.parent_id
        return any(search in (name or "").lower() for name in names)

    def action_open_adjacent_account(self, options, direction):
        """Open the general ledger on the account before or after the one
        currently searched in the search bar."""
        report = self.env["account.report"].browse(options["report_id"])
        codes = self._get_navigation_account_codes(report, options)
        search = (options.get("filter_search_bar") or "").strip()

        # The search bar holds the account code when the ledger is opened from
        # the trial balance. Any other text still works: the codes are then
        # compared to it alphabetically.
        if direction == "next":
            code = next((code for code in codes if not search or code > search), None)
        else:
            code = next((code for code in reversed(codes) if not search or code < search), None)

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

        action = self.env["ir.actions.actions"]._for_xml_id("account_reports.action_account_report_general_ledger")
        action["params"] = {"options": new_options, "ignore_session": True}
        # The search bar input is filled from this context key on load.
        action["context"] = dict(ast.literal_eval(action["context"]), default_filter_accounts=code)
        action["name"] = action["display_name"] = f"{action['name']} - {code}"
        return action
