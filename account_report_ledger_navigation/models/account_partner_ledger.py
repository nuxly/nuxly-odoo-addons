from odoo import _, models


class AccountPartnerLedgerReportHandler(models.AbstractModel):
    _inherit = "account.partner.ledger.report.handler"

    def _custom_options_initializer(self, report, options, previous_options):
        super()._custom_options_initializer(report, options, previous_options=previous_options)
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
        one: the partner selected in the "Partners" filter, or else the first
        partner matching the search bar."""
        report = self.env["account.report"].browse(options["report_id"])
        partners = self._get_navigation_partners(report, options)

        current = self.env["res.partner"]
        if len(options.get("partner_ids") or []) == 1:
            current = partners.filtered(lambda partner: partner.id == options["partner_ids"][0])
        elif search := (options.get("filter_search_bar") or "").strip().lower():
            current = partners.filtered(lambda partner: search in (partner.display_name or "").lower())[:1]

        if current:
            index = partners.ids.index(current.id) + (1 if direction == "next" else -1)
            partner = partners[index] if 0 <= index < len(partners) else self.env["res.partner"]
        else:
            partner = partners[:1] if direction == "next" else partners[-1:]

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

        action = self.env["ir.actions.actions"]._for_xml_id("account_reports.action_account_report_partner_ledger")
        action["params"] = {"options": new_options, "ignore_session": True}
        return action
