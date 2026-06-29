from odoo import fields, models, _
from odoo.exceptions import UserError


class HrExpense(models.Model):
    _inherit = "hr.expense"

    is_ik_expense = fields.Boolean(related="product_id.is_ik_expense", help="Indicates whether the selected expense product is configured as a mileage allowance product.")
    ik_vehicle_id = fields.Many2one("fleet.vehicle", string="Mileage vehicle", help="Vehicle used for the mileage allowance trip.")
    ik_origin_address = fields.Char(string="Departure address", help="Departure address entered by the employee in the mileage trip wizard.")
    ik_destination_address = fields.Char(string="Arrival address", help="Arrival address entered by the employee in the mileage trip wizard.")
    ik_google_origin_address = fields.Char(string="Google departure address", help="Departure address normalized and returned by the Google Maps API.")
    ik_google_destination_address = fields.Char(string="Google arrival address", help="Arrival address normalized and returned by the Google Maps API.")
    ik_trip_type = fields.Selection([("one_way", "One way"), ("round_trip", "Round trip")], string="Trip type", help="Indicates whether the mileage trip is one way or round trip.")
    ik_distance = fields.Float(string="Mileage distance", digits=(16, 2), help="Distance in kilometers used for the mileage allowance calculation.")

    def action_open_ik_trip_wizard(self):
        """
        Open the mileage trip wizard from an expense.

        The wizard is only available for expenses using a product marked as a
        mileage allowance product. The computed trip data is later written back
        on the expense because wizard records are temporary.
        """
        self.ensure_one()
        if not self.is_ik_expense:
            raise UserError(_("This expense is not a mileage allowance expense."))
        if not self.employee_id:
            raise UserError(_("Please select an employee before entering a mileage trip."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Mileage Trip"),
            "res_model": "hr.expense.ma.trip.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_expense_id": self.id},
        }