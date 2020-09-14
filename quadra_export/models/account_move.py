from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    exported_date = fields.Datetime('Exported date', help="If a date, so the account item was exported.")
