from odoo import fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class HrExpense(models.Model):
    _inherit = "hr.expense"

    is_ik_expense = fields.Boolean(related="product_id.is_ik_expense", help="Indicates whether the selected expense product is configured as a mileage allowance product.")
    ik_vehicle_id = fields.Many2one("fleet.vehicle", string="Mileage vehicle", help="Vehicle used for the mileage allowance trip.")
    ik_origin_address = fields.Char(string="Departure address", help="Departure address entered by the employee in the mileage trip wizard.")
    ik_destination_address = fields.Char(string="Arrival address", help="Arrival address entered by the employee in the mileage trip wizard.")
    ik_google_origin_address = fields.Char(string="Google departure address", help="Departure address normalized and returned by the Google Maps API.")
    ik_google_destination_address = fields.Char(string="Google arrival address", help="Arrival address normalized and returned by the Google Maps API.")
    ik_trip_type = fields.Selection([("one_way", "One way"), ("round_trip", "Round trip")], string="Trip type", help="Indicates whether the mileage trip is one way or round trip.")
    ik_distance = fields.Float(string="Mileage distance (km)", digits=(16, 2), help="Distance in kilometers used for the mileage allowance calculation.")
    ik_scale_id = fields.Many2one("hr.expense.ma.scale", string="Mileage scale", readonly=True, help="Mileage allowance scale used to compute this expense.",)
    ik_previous_year_distance = fields.Float(string="Previous yearly distance (km)", readonly=True, help="Employee yearly mileage before this expense.",)
    ik_new_year_distance = fields.Float(string="New yearly distance (km)", readonly=True, help="Employee yearly mileage after adding this expense distance.",)
    ik_counter_updated = fields.Boolean(string="Mileage counter updated", readonly=True, help="Indicates whether this expense has already updated the employee yearly mileage counter.",)

    def action_open_ik_trip_wizard(self):
        """
        Open the mileage trip wizard from an expense.

        The wizard is only available for expenses using a product marked as a
        mileage allowance product. The computed trip data is later written back
        on the expense because wizard records are temporary.
        """
        self.ensure_one()
        _logger.info("IK action_open_ik_trip_wizard - expense=%s employee=%s", self.id, self.employee_id)
        if not self.is_ik_expense:
            _logger.warning("IK action_open_ik_trip_wizard - expense=%s is not a mileage expense", self.id)
            raise UserError(_("This expense is not a mileage allowance expense."))
        if not self.employee_id:
            _logger.warning("IK action_open_ik_trip_wizard - expense=%s has no employee", self.id)
            raise UserError(_("Please select an employee before entering a mileage trip."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Mileage Trip"),
            "res_model": "hr.expense.ma.trip.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_expense_id": self.id},
        }

    def _get_ik_counter_year(self):
        """Return the mileage counter year based on the expense date."""
        self.ensure_one()
        year = self.date.year
        _logger.info("IK get_counter_year - expense=%s date=%s year=%s", self.id, self.date, year)
        return year

    def _get_ik_scale(self, yearly_distance):
        """Find the mileage scale matching the expense context."""
        self.ensure_one()
        vehicle = self.ik_vehicle_id
        fiscal_power = vehicle.horsepower
        _logger.info(
            "IK get_scale - expense=%s vehicle=%s vehicle_type=%s fuel_type=%s fiscal_power=%s yearly_distance=%s",
            self.id, vehicle, vehicle.vehicle_type, vehicle.fuel_type, fiscal_power, yearly_distance,
        )
        scale = self.env["hr.expense.ma.scale"].search(
            [
                ("start_date", "<=", self.date),
                ("vehicle_type", "=", vehicle.vehicle_type),
                ("fuel_type_ids.code", "=", vehicle.fuel_type),
                ("horsepower_min", "<=", fiscal_power),
                "|",
                ("horsepower_max", "=", False),
                ("horsepower_max", ">=", fiscal_power),
                ("distance_min", "<=", yearly_distance),
                "|",
                ("distance_max", "=", False),
                ("distance_max", ">=", yearly_distance),
            ], order="start_date desc", limit=1,)
        _logger.info("IK get_scale - found scale=%s", scale)
        if not scale:
            _logger.warning("IK get_scale - no scale found for expense=%s", self.id)
            raise UserError(_("No mileage allowance scale was found."))
        return scale

    def _compute_ik_amount(self):
        """Compute the mileage allowance amount."""
        self.ensure_one()
        _logger.info("IK compute_ik_amount - start expense=%s distance=%s", self.id, self.ik_distance)
        year = self._get_ik_counter_year()
        previous_distance = (
            self.employee_id.ik_km_by_year or {}
        ).get(str(year), 0)
        new_distance = previous_distance + self.ik_distance
        _logger.info(
            "IK compute_ik_amount - year=%s previous_distance=%s new_distance=%s",
            year, previous_distance, new_distance,
        )
        new_scale = self._get_ik_scale(new_distance)
        new_amount = new_scale._compute_amount(new_distance)
        previous_amount = 0
        if previous_distance:
            previous_scale = self._get_ik_scale(previous_distance)
            previous_amount = previous_scale._compute_amount(previous_distance)
        amount = new_amount - previous_amount
        _logger.info(
            "IK compute_ik_amount - new_amount=%s previous_amount=%s final_amount=%s",
            new_amount, previous_amount, amount,
        )
        self.write({
            "ik_scale_id": new_scale.id,
            "ik_previous_year_distance": previous_distance,
            "ik_new_year_distance": new_distance,
            "price_unit": amount,
            "quantity": 1,
            "total_amount_currency": amount,
        })

    def _update_ik_employee_counter(self):
        """Update employee yearly mileage counter after validation."""
        for expense in self.filtered(lambda e: e.is_ik_expense and not e.ik_counter_updated):
            year = expense._get_ik_counter_year()
            data = dict(expense.employee_id.ik_km_by_year or {})
            data[str(year)] = (
                data.get(str(year), 0) + expense.ik_distance)
            _logger.info(
                "IK update_ik_employee_counter - expense=%s employee=%s year=%s new_total=%s",
                expense.id, expense.employee_id, year, data[str(year)],
            )
            expense.employee_id.ik_km_by_year = data
            expense.ik_counter_updated = True

    def write(self, vals):
        """Update the yearly mileage counter when an IK expense reaches the posted state."""
        res = super().write(vals)
        to_update = self.filtered(
            lambda e: e.is_ik_expense
            and e.state == "posted"
            and not e.ik_counter_updated
        )
        if to_update:
            _logger.info("IK write - updating mileage counter for expenses=%s", to_update.ids)
        to_update._update_ik_employee_counter()
        return res
