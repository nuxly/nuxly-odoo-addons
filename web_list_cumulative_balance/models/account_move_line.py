# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # Non-stored anchor field: the real cumulative balance is computed live in the browser (based on the rows and selection currently on screen).
    # This field only exists so a widget can be attached to it in the view.
    x_cumulative_balance = fields.Monetary(string="Cumulative Balance", currency_field="company_currency_id", compute="_compute_x_cumulative_balance", help="Running total of the Balance column, in the order shown on screen. If some lines are selected, only they count towards the total.")

    def _compute_x_cumulative_balance(self):
        # Never actually read: the widget ignores this value and computes its own
        # total from the rows on screen. This only keeps the field non-empty in
        # case the widget's JS fails to load for any reason.
        for line in self:
            line.x_cumulative_balance = line.balance
