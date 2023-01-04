from odoo import api, fields, models, _

class HrEmployeePrivate(models.Model):
    _inherit = 'hr.employee'

    ignore_timesheet_reminder = fields.Boolean(string='Ignore timesheet reminder', store=True,
         help="Do not send timesheet mail reminder if checked", groups="hr.group_hr_user", tracking=True)