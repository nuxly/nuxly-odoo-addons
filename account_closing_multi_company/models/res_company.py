from odoo import models, _


class ResCompany(models.Model):
    _inherit = "res.company"

    def action_open_closing_multi_wizard(self):
        return {
            "type": "ir.actions.act_window",
            "name": _("Lock journal entries"),
            "res_model": "account.change.lock.date",
            "view_mode": "form",
            "target": "new",
            "context": {"active_model": "res.company", "active_ids": self.ids},
        }
