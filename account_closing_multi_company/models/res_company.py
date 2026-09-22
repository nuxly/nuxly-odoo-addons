from odoo import models, _


class ResCompany(models.Model):
    _inherit = "res.company"

    def action_open_closing_multi_wizard(self):
        return {
            "type": "ir.actions.act_window",
            "name": _("Period Closing"),
            "res_model": "account.closing.multi.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"active_model": "res.company", "active_ids": self.ids},
        }
