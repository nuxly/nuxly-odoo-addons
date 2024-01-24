from odoo import models, _

class HrEmployeePrivate(models.Model):
    _inherit = "res.users"

    # Return the different time tables of a given manager
    def get_summarized_analytic_lines(self, manager):
        return self.env['timesheet.summary'].get_summarized_analytic_lines(manager)