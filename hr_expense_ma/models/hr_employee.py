from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    ik_km_by_year = fields.Json(string="Mileage allowance kilometers by year", groups="hr.group_hr_user", help="Stores the employee yearly mileage allowance kilometers as a dictionary keyed by year.")
    ik_km_by_year_display = fields.Text(string="Mileage allowance summary", compute="_compute_ik_km_by_year_display")

    def _compute_ik_km_by_year_display(self):
        for employee in self:
            employee.ik_km_by_year_display = "\n".join(
                f"{year} : {km} km" for year, km in sorted((employee.ik_km_by_year or {}).items()))
