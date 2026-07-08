import logging
import requests

_logger = logging.getLogger(__name__)

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrExpenseMaTripWizard(models.TransientModel):
    _name = "hr.expense.ma.trip.wizard"
    _description = "Mileage allowance trip wizard"

    expense_id = fields.Many2one("hr.expense", required=True, help="Expense on which the mileage trip data will be applied.")
    employee_id = fields.Many2one("hr.employee", string="Employee", related="expense_id.employee_id", readonly=True, store=False, help="Employee linked to the expense.")
    available_vehicle_ids = fields.Many2many("fleet.vehicle", compute="_compute_available_vehicle_ids", help="Personal vehicles available for the employee.")
    vehicle_id = fields.Many2one("fleet.vehicle", string="Vehicle", required=True, domain="[('id', 'in', available_vehicle_ids)]", help="Personal vehicle used for the mileage allowance trip.")
    origin_address = fields.Char(string="Departure address", help="Departure address used to compute the trip distance.")
    destination_address = fields.Char(string="Arrival address", help="Arrival address used to compute the trip distance.")
    trip_type = fields.Selection([("one_way", "One way"), ("round_trip", "Round trip")], string="Trip type", default="one_way", required=True, help="Select whether the trip is one way or round trip.")
    origin_type = fields.Selection([("home", "Home"), ("work", "Work"), ("other", "Other")], string="Departure type", default="other", required=True, help="Suggested source used to fill the departure address.")
    destination_type = fields.Selection([("home", "Home"), ("work", "Work"), ("other", "Other")], string="Arrival type", default="other", required=True, help="Suggested source used to fill the arrival address.")    
    distance = fields.Float(string="Distance (km)", digits=(16, 2), readonly=True, help="Computed distance in kilometers.")
    google_origin_address = fields.Char(string="Google departure address", readonly=True, help="Departure address normalized and returned by the Google Maps API.")
    google_destination_address = fields.Char(string="Google arrival address", readonly=True, help="Arrival address normalized and returned by the Google Maps API.")

    @api.depends("employee_id")
    def _compute_available_vehicle_ids(self):
        """
        Compute the list of personal vehicles available for the expense employee.

        The wizard must only allow vehicles marked as personal and assigned to
        the employee. This prevents using another employee's vehicle for the
        mileage allowance calculation.
        """
        for wizard in self:
            wizard.available_vehicle_ids = wizard.employee_id._get_ik_personal_vehicles() if wizard.employee_id else False

    @api.model
    def default_get(self, fields_list):
        """
        Initialize the wizard from the active expense.

        If the employee has exactly one personal vehicle, it is selected by
        default. If several vehicles are available, the user must choose one.
        """
        res = super().default_get(fields_list)
        expense = self.env["hr.expense"].browse(res.get("expense_id") or self.env.context.get("default_expense_id"))
        if expense:
            res["expense_id"] = expense.id
            vehicles = expense.employee_id._get_ik_personal_vehicles() if expense.employee_id else self.env["fleet.vehicle"]
            if len(vehicles) == 1:
                res["vehicle_id"] = vehicles.id
        return res

    def action_compute_distance(self):
        """
        Compute the trip distance using Google Distance Matrix API.

        The API returns both the distance and normalized addresses. The normalized
        addresses are stored to keep the exact values used for the calculation.
        If the trip is marked as round trip, the computed distance is doubled.
        """
        self.ensure_one()
        if not self.origin_address:
            raise UserError(_("Please select or enter a departure address."))
        if not self.destination_address:
            raise UserError(_("Please select or enter an arrival address."))
        api_key = self.env["ir.config_parameter"].sudo().get_param("google_address_autocomplete.google_places_api_key")
        if not api_key:
            raise UserError(_("Please configure the Google Places API key in the general settings."))

        data = self._get_google_distance(api_key)
        distance = data["distance_km"] * (2 if self.trip_type == "round_trip" else 1)
        self.write({
            "distance": distance,
            "google_origin_address": data["origin_address"],
            "google_destination_address": data["destination_address"],
        })

        return {
            "type": "ir.actions.act_window",
            "name": _("Mileage Trip"),
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def _get_google_distance(self, api_key):
        """
        Call Google Distance Matrix API and return normalized trip information.

        The method keeps the external API handling isolated from the button
        action so the parsing and error management can be reused or replaced
        later if another distance provider is introduced.
        """
        response = requests.get(
            "https://maps.googleapis.com/maps/api/distancematrix/json",
            params={
                "origins": self.origin_address,
                "destinations": self.destination_address,
                "key": api_key,
                "units": "metric",
                "language": "fr",
                "region": "fr",
            },
            timeout=15,
        )
        response.raise_for_status()
        result = response.json()

        if result.get("status") != "OK":
            raise UserError(_("Google Maps API error: %s") % result.get("status"))

        element = result["rows"][0]["elements"][0]
        if element.get("status") != "OK":
            raise UserError(_("Unable to compute the distance for this trip: %s") % element.get("status"))

        return {
            "distance_km": element["distance"]["value"] / 1000,
            "origin_address": result["origin_addresses"][0],
            "destination_address": result["destination_addresses"][0],
        }

    def action_apply(self):
        """
        Apply the computed trip information on the expense.

        Wizard records are temporary, so all data required for accounting,
        validation and later mileage allowance calculation must be stored on
        the related expense before closing the wizard.
        """
        self.ensure_one()
        if not self.distance:
            raise UserError(_("Please compute the distance before applying the trip."))

        self.expense_id.write({
            "ik_vehicle_id": self.vehicle_id.id,
            "ik_origin_address": self.origin_address,
            "ik_destination_address": self.destination_address,
            "ik_google_origin_address": self.google_origin_address,
            "ik_google_destination_address": self.google_destination_address,
            "ik_trip_type": self.trip_type,
            "ik_distance": self.distance,
        })
        self.expense_id._compute_ik_amount()

    @api.onchange("origin_type")
    def _onchange_origin_type(self):
        """Fill the departure address from employee home or work address when requested."""
        _logger.warning(
            "IK origin onchange - type=%s employee=%s",
            self.origin_type,
            self.employee_id,
        )

        if not self.employee_id:
            self.origin_address = False
        elif self.origin_type == "home":
            self.origin_address = self.employee_id._get_ik_home_address()
        elif self.origin_type == "work":
            self.origin_address = self.employee_id._get_ik_work_address()
        elif self.origin_type == "other":
            self.origin_address = False

        _logger.warning(
            "IK origin onchange - address=%s",
            self.origin_address,
        )


    @api.onchange("destination_type")
    def _onchange_destination_type(self):
        """Fill the arrival address from employee home or work address when requested."""
        _logger.warning(
            "IK destination onchange - type=%s employee=%s",
            self.destination_type,
            self.employee_id,
        )

        if not self.employee_id:
            self.destination_address = False
        elif self.destination_type == "home":
            self.destination_address = self.employee_id._get_ik_home_address()
        elif self.destination_type == "work":
            self.destination_address = self.employee_id._get_ik_work_address()
        elif self.destination_type == "other":
            self.destination_address = False

        _logger.warning(
            "IK destination onchange - address=%s",
            self.destination_address,
        )
