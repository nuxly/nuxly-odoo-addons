from odoo import models


class AccountReport(models.Model):
    _inherit = "account.report"

    def caret_option_open_general_ledger(self, options, params):
        action = super().caret_option_open_general_ledger(options, params)
        # Accounts shown on screen by the search bar of the report the ledger
        # is opened from (trial balance...), sent by the client: the previous
        # / next buttons of the general ledger only go through them.
        if options.get("ledger_navigation_visible_account_ids") is not None:
            gl_options = action["params"]["options"]
            gl_options["ledger_navigation_account_ids"] = options["ledger_navigation_visible_account_ids"]
            gl_options["ledger_navigation_group_ids"] = options.get("ledger_navigation_matched_group_ids") or []
        # Tells the general ledger it is not opened from the menu, see
        # AccountGeneralLedgerReportHandler._custom_options_initializer().
        action["context"]["ledger_navigation"] = True
        return action
