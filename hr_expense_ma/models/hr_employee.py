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


    def _get_ik_home_address(self):
        """Return the employee private address formatted for distance calculation."""
        self.ensure_one()
        return self._format_ik_address(self.private_street, self.private_street2, self.private_zip, self.private_city, self.private_country_id.name)

    def _get_ik_work_address(self):
        """Return the employee work address formatted for distance calculation."""
        self.ensure_one()
        partner = self.address_id
        return self._format_ik_address(partner.street, partner.street2, partner.zip, partner.city, partner.country_id.name) if partner else False

    def _format_ik_address(self, *parts):
        """Build a single address string from non-empty address parts."""
        return ", ".join(part for part in parts if part)