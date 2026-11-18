import ast
import logging

from odoo import _, models

_logger = logging.getLogger(__name__)


class AccountPartnerLedgerReportHandler(models.AbstractModel):
    _inherit = "account.partner.ledger.report.handler"

    def _custom_options_initializer(self, report, options, previous_options):
        super()._custom_options_initializer(report, options, previous_options=previous_options)
        # Odoo restores the last options of the report from the browser
        # session when it is opened again from the menu, including the
        # partner set in the "Partners" filter by the navigation and the
        # search bar text (while the search bar input itself stays empty).
        # Opened from the menu, the ledger must show the list again: the
        # partner filter is given back its value from before the navigation,
        # and the hidden search and the navigation state are dropped. They are
        # kept when the ledger is opened by the navigation buttons
        # ("ledger_navigation" context key), and when coming back through the
        # breadcrumb (where is_opening_report is not set).
        if previous_options.get("is_opening_report") and not self.env.context.get("ledger_navigation"):
            navigation_partner_id = previous_options.get("ledger_navigation_partner_id")
            if navigation_partner_id and options.get("partner_ids") == [navigation_partner_id]:
                partners = self.env["res.partner"].with_context(active_test=False).search(
                    [("id", "in", previous_options.get("ledger_navigation_selected_partner_ids") or [])]
                )
                options["partner_ids"] = partners.ids
                options["selected_partner_ids"] = partners.mapped("display_name")
            if navigation_partner_id or options.get("filter_search_bar"):
                _logger.info(
                    "Ledger navigation - partner ledger opened from the menu: navigation partner %s and hidden search %r "
                    "dropped, partner filter set back to %s",
                    navigation_partner_id, options.get("filter_search_bar"), options.get("partner_ids"),
                )
            options.pop("filter_search_bar", None)
        else:
            # Kept from one ledger to the next, see action_open_adjacent_partner().
            for key in ("ledger_navigation_partner_id", "ledger_navigation_partner_ids", "ledger_navigation_selected_partner_ids"):
                if previous_options.get(key):
                    options[key] = previous_options[key]
        # "replace_current_action" makes the client open the next ledger in
        # place of the current one, instead of stacking a new breadcrumb at
        # every click (see account_report_controller.esm.js).
        options["buttons"] += [
            {
                "name": _("Previous partner"),
                "sequence": 200,
                "action": "action_open_adjacent_partner",
                "action_param": "previous",
                "always_show": True,
                "branch_allowed": True,
                "replace_current_action": True,
            },
            {
                "name": _("Next partner"),
                "sequence": 210,
                "action": "action_open_adjacent_partner",
                "action_param": "next",
                "always_show": True,
                "branch_allowed": True,
                "replace_current_action": True,
            },
        ]

    def _get_navigation_partners(self, report, options):
        """Return the partners listed by the partner ledger for these options,
        once the partner filter and the search bar are removed, in the same
        order as the ledger. The "Unknown partner" line is left out.
        """
        options = {**options, "partner_ids": []}
        options.pop("filter_search_bar", None)
        # _query_partners() joins the currency temporary table, which is only
        # created when the report lines are computed.
        report._init_currency_table(options)
        partners = self.env["res.partner"]
        for partner, _values in self._query_partners(report, options):
            if partner:
                partners |= partner
        return partners

    def action_open_adjacent_partner(self, options, direction):
        """Open the partner ledger on the partner before or after the current
        one, among the partners the ledger shows.

        - A single partner selected in the "Partners" filter is the current
          one. If it was reached from a filtered list, the navigation stays
          within that list, as long as the partner still belongs to it.
        - Otherwise, the list is the one currently shown: the partners of
          the "Partners" filter, and with a search bar text, the partners
          shown on screen, sent by the client (the search is applied there,
          to journal items too). The navigation starts from its first (or
          last) partner. A list of only one partner makes it the current one.
        """
        report = self.env["account.report"].browse(options["report_id"])
        all_partners = self._get_navigation_partners(report, options)
        selected_ids = options.get("partner_ids") or []
        search = (options.get("filter_search_bar") or "").strip()
        visible_partner_ids = options.get("ledger_navigation_visible_partner_ids") or []

        current = self.env["res.partner"]
        if len(selected_ids) == 1:
            current = all_partners.filtered(lambda partner: partner.id == selected_ids[0])
            navigation_partner_ids = options.get("ledger_navigation_partner_ids")
            selection = options.get("ledger_navigation_selected_partner_ids")
            partners = all_partners
            if navigation_partner_ids:
                partners = all_partners.filtered(lambda partner: partner.id in navigation_partner_ids)
            if not current & partners:
                navigation_partner_ids = selection = None
                partners = all_partners
        else:
            selection = selected_ids
            partners = all_partners
            if selected_ids:
                partners = partners.filtered(lambda partner: partner.id in selected_ids)
            if search:
                partners = partners.filtered(lambda partner: partner.id in visible_partner_ids)
            navigation_partner_ids = partners.ids
            if len(partners) == 1:
                current = partners

        if current:
            index = partners.ids.index(current.id) + (1 if direction == "next" else -1)
            partner = partners[index] if 0 <= index < len(partners) else self.env["res.partner"]
        else:
            partner = partners[:1] if direction == "next" else partners[-1:]

        _logger.info(
            "Ledger navigation - partner ledger %s: partner filter=%s search=%r, partners shown on screen=%s, "
            "%s partners in the ledger, %s in the navigation list %s, current=%s -> %s",
            direction, selected_ids, search, visible_partner_ids,
            len(all_partners), len(partners), partners.mapped("name"), current.name, partner.name,
        )

        if not partner:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "type": "info",
                    "message": _("This is the last partner.") if direction == "next" else _("This is the first partner."),
                },
            }

        new_options = report.get_options({**options, "partner_ids": [partner.id]})
        new_options.pop("filter_search_bar", None)
        new_options["unfold_all"] = True
        # The partner filter set here is undone when the ledger is opened
        # again from the menu, see _custom_options_initializer().
        new_options["ledger_navigation_partner_id"] = partner.id
        new_options["ledger_navigation_partner_ids"] = navigation_partner_ids or None
        new_options["ledger_navigation_selected_partner_ids"] = selection or None

        action = self.env["ir.actions.actions"]._for_xml_id("account_reports.action_account_report_partner_ledger")
        action["params"] = {"options": new_options, "ignore_session": True}
        action["context"] = dict(ast.literal_eval(action["context"]), ledger_navigation=True)
        action["name"] = action["display_name"] = f"{action['name']} - {partner.display_name}"
        return action
