from odoo import _, models


class AccountPartnerLedgerReportHandler(models.AbstractModel):
    _inherit = "account.partner.ledger.report.handler"

    def _custom_options_initializer(self, report, options, previous_options):
        super()._custom_options_initializer(report, options, previous_options=previous_options)
        # Kept from one ledger to the next, see action_open_adjacent_partner().
        for key in ("ledger_navigation_search", "ledger_navigation_partner_ids"):
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

    def _filter_navigation_partners(self, partners, search, partner_ids):
        """Keep the partners the ledger shows with this search bar text (the
        partner line name contains it, like on the client side) and this
        "Partners" filter selection."""
        if search:
            partners = partners.filtered(lambda partner: search.lower() in (partner.name or "").lower())
        if partner_ids:
            partners = partners.filtered(lambda partner: partner.id in partner_ids)
        return partners

    def action_open_adjacent_partner(self, options, direction):
        """Open the partner ledger on the partner before or after the current
        one, among the partners the ledger shows.

        - A single partner selected in the "Partners" filter is the current
          one. If it was reached from a filtered list (search bar or several
          partners selected), the navigation stays within that list, as long
          as the partner still belongs to it.
        - Otherwise, the list is the one currently shown, filtered by the
          search bar and the "Partners" filter, and the navigation starts
          from its first (or last) partner. A list of only one partner makes
          it the current one.
        """
        report = self.env["account.report"].browse(options["report_id"])
        partners = self._get_navigation_partners(report, options)
        selected_ids = options.get("partner_ids") or []

        current = self.env["res.partner"]
        if len(selected_ids) == 1:
            current = partners.filtered(lambda partner: partner.id == selected_ids[0])
            search = options.get("ledger_navigation_search")
            partner_ids = options.get("ledger_navigation_partner_ids")
            filtered = self._filter_navigation_partners(partners, search, partner_ids)
            if current & filtered:
                partners = filtered
            else:
                search = partner_ids = None
        else:
            search = (options.get("filter_search_bar") or "").strip()
            partner_ids = selected_ids
            partners = self._filter_navigation_partners(partners, search, partner_ids)
            if len(partners) == 1:
                current = partners

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
        new_options["ledger_navigation_search"] = search or None
        new_options["ledger_navigation_partner_ids"] = partner_ids or None

        action = self.env["ir.actions.actions"]._for_xml_id("account_reports.action_account_report_partner_ledger")
        action["params"] = {"options": new_options, "ignore_session": True}
        action["name"] = action["display_name"] = f"{action['name']} - {partner.display_name}"
        return action
