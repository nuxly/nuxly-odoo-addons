from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    ik_km_by_year = fields.Json(string="Mileage allowance kilometers by year", groups="hr.group_hr_user", help="Stores the employee yearly mileage allowance kilometers as a dictionary keyed by year.")
    ik_km_by_year_display = fields.Text(string="Mileage allowance summary", compute="_compute_ik_km_by_year_display")

    def _compute_ik_km_by_year_display(self):
        for employee in self:
            employee.ik_km_by_year_display = "\n".join(
                f"{year} : {km:.2f} km" for year, km in sorted((employee.ik_km_by_year or {}).items()))

    def _get_ik_personal_vehicles(self):
        """
        Return personal vehicles assigned to the employee.

        Mileage allowance calculations can only be performed using vehicles
        identified as personal vehicles and linked to the employee through
        Fleet. This helper centralizes the vehicle selection logic so it can
        be reused across mileage allowance features.
        """
        self.ensure_one()
        return self.env["fleet.vehicle"].search([
            ("driver_employee_id", "=", self.id),
            ("is_personal_vehicle", "=", True),
        ])


    def _get_ik_home_address_parts(self):
        """Return the employee private address split into its individual components."""
        self.ensure_one()
        return {
            "street": self.private_street,
            "city": self.private_city,
            "zip": self.private_zip,
            "country_id": self.private_country_id or self.company_id.country_id,
        }

    def _get_ik_work_address_parts(self):
        """Return the employee work address split into its individual components."""
        self.ensure_one()
        partner = self.address_id
        return {
            "street": partner.street,
            "city": partner.city,
            "zip": partner.zip,
            "country_id": partner.country_id or self.company_id.country_id,
        }

    def _format_ik_address(self, *parts):
        """Build a single address string from non-empty address parts."""
        return ", ".join(part for part in parts if part)