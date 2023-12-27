#-*- coding:utf-8 -*-

from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    exported_date = fields.Date(string='Exported Date', readonly=True, copy=False, help="Date when the accounting entry was exported.")

    # Mark the accounting entry as exported by setting the export date
    def mark_exported(self):
        self.write({'exported_date': fields.Date.today()})
