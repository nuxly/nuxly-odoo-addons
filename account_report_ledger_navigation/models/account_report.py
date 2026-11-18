from odoo import models


class AccountReport(models.Model):
    _inherit = "account.report"

    def caret_option_open_general_ledger(self, options, params):
        action = super().caret_option_open_general_ledger(options, params)
        gl_options = action["params"]["options"]
        # Text searched in the trial balance: the previous / next buttons of
        # the general ledger only go through the accounts it matches.
        if self._get_custom_handler_model() == "account.trial.balance.report.handler" and options.get("filter_search_bar"):
            gl_options["ledger_navigation_search"] = options["filter_search_bar"]
        action["name"] = action["display_name"] = f"{action['name']} - {gl_options['filter_search_bar']}"
        return action
