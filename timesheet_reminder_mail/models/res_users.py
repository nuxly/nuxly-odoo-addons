from odoo import api, fields, models, _

class HrEmployeePrivate(models.Model):
    _inherit = "res.users"

    # Retoune les différents tableaux de temps d'un manager
    def get_summarized_analytic_lines(self, manager):
        summary = self.env['timesheet.summary']
        return summary.get_summarized_analytic_lines(manager)