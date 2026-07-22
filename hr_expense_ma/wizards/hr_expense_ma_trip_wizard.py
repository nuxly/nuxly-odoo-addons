import logging

import requests

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HrExpenseMaTripWizard(models.TransientModel):
    _name = "hr.expense.ma.trip.wizard"
    _description = "Mileage allowance trip wizard"

    expense_id = fields.Many2one("hr.expense", required=True, help="Expense on which the mileage trip data will be applied.")
    employee_id = fields.Many2one("hr.employee", string="Employee", related="expense_id.employee_id", readonly=True, store=False, help="Employee linked to the expense.")
    available_vehicle_ids = fields.Many2many("fleet.vehicle", compute="_compute_available_vehicle_ids", help="Personal vehicles available for the employee.")
    vehicle_id = fields.Many2one("fleet.vehicle", string="Vehicle", required=True, domain="[('id', 'in', available_vehicle_ids)]", help="Personal vehicle used for the mileage allowance trip.")
    origin_street = fields.Char(string="Departure street", help="Departure street used to compute the trip distance.")
    destination_street = fields.Char(string="Arrival street", help="Arrival street used to compute the trip distance.")
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
            _logger.info(
                "IK compute_available_vehicle_ids - employee=%s vehicles=%s",
                wizard.employee_id, wizard.available_vehicle_ids.ids,
            )

    @api.model
    def default_get(self, fields_list):
        """
        Initialize the wizard from the active expense.

        If the employee has exactly one personal vehicle, it is selected by
        default. If several vehicles are available, the user must choose one.
        """
        res = super().default_get(fields_list)
        expense = self.env["hr.expense"].browse(res.get("expense_id") or self.env.context.get("default_expense_id"))
        _logger.info("IK default_get - expense=%s employee=%s", expense, expense.employee_id if expense else False)
        if expense:
            res["expense_id"] = expense.id
            vehicles = expense.employee_id._get_ik_personal_vehicles() if expense.employee_id else self.env["fleet.vehicle"]
            _logger.info("IK default_get - available personal vehicles=%s", vehicles.ids)
            if len(vehicles) == 1:
                res["vehicle_id"] = vehicles.id
                _logger.info("IK default_get - auto-selected vehicle=%s", vehicles)
        return res

    def _get_ik_trip_address_parts(self, address_type, manual_parts):
        """
        Resolve the address components to use for the trip based on the selected address type.

        The departure/arrival address fields are readonly in the form when a
        "home" or "work" type is selected, so values set on them by the
        onchange are only used for display and are not reliably saved by the
        web client. The actual components must therefore be resolved again
        here instead of relying on the stored field values.
        """
        if address_type == "home":
            parts = self.employee_id._get_ik_home_address_parts()
        elif address_type == "work":
            parts = self.employee_id._get_ik_work_address_parts()
        else:
            parts = manual_parts
        _logger.info("IK get_trip_address_parts - type=%s parts=%s", address_type, parts)
        return parts

    def _get_ik_wizard_address_parts(self, prefix):
        """Return the current wizard field values for the given address prefix ("origin"/"destination")."""
        parts = {
            "street": self[f"{prefix}_street"],
        }
        _logger.info("IK get_wizard_address_parts - prefix=%s parts=%s", prefix, parts)
        return parts

    def _format_ik_trip_address(self, address_type, parts):
        """
        Compose a single address string from its individual components.

        For "other" addresses, the street value already holds the full
        address string selected through the Google autocomplete widget, so
        it is used as is instead of being recomposed with the country, which
        would otherwise be duplicated in the resulting address.
        """
        if address_type == "other":
            address = parts.get("street") or ""
        else:
            country = parts.get("country_id")
            address = self.employee_id._format_ik_address(
                parts.get("street"), parts.get("zip"), parts.get("city"), country.name if country else False,
            )
        _logger.info("IK format_trip_address - type=%s parts=%s -> address=%s", address_type, parts, address)
        return address

    def _compute_ik_trip_distance(self):
        """
        Compute the trip distance using Google Distance Matrix API.

        The API returns both the distance and normalized addresses. The normalized
        addresses are stored to keep the exact values used for the calculation.
        If the trip is marked as round trip, the computed distance is doubled.
        """
        self.ensure_one()
        _logger.info(
            "IK compute_ik_trip_distance - start wizard=%s origin_type=%s destination_type=%s trip_type=%s",
            self.id, self.origin_type, self.destination_type, self.trip_type,
        )
        origin_parts = self._get_ik_trip_address_parts(self.origin_type, self._get_ik_wizard_address_parts("origin"))
        destination_parts = self._get_ik_trip_address_parts(self.destination_type, self._get_ik_wizard_address_parts("destination"))
        origin_address = self._format_ik_trip_address(self.origin_type, origin_parts)
        destination_address = self._format_ik_trip_address(self.destination_type, destination_parts)
        _logger.info(
            "IK compute_ik_trip_distance - resolved origin=%r destination=%r",
            origin_address, destination_address,
        )
        if not origin_address:
            _logger.warning("IK compute_ik_trip_distance - missing departure address")
            raise UserError(_("Please select or enter a departure address."))
        if not destination_address:
            _logger.warning("IK compute_ik_trip_distance - missing arrival address")
            raise UserError(_("Please select or enter an arrival address."))

        api_key = self.env["ir.config_parameter"].sudo().get_param("google_address_autocomplete.google_places_api_key")
        if not api_key:
            _logger.warning("IK compute_ik_trip_distance - missing Google Places API key")
            raise UserError(_("Please configure the Google Places API key in the general settings."))

        data = self._get_google_distance(api_key, origin_address, destination_address)
        distance = data["distance_km"] * (2 if self.trip_type == "round_trip" else 1)
        _logger.info("IK compute_ik_trip_distance - computed distance=%s km (trip_type=%s)", distance, self.trip_type)
        vals = {
            "distance": distance,
            "google_origin_address": data["origin_address"],
            "google_destination_address": data["destination_address"],
        }
        if self.origin_type != "other":
            vals.update({
                "origin_street": origin_address,
            })
        if self.destination_type != "other":
            vals.update({
                "destination_street": destination_address,
            })
        _logger.info("IK compute_ik_trip_distance - writing vals=%s", vals)
        self.write(vals)

    def _get_google_distance(self, api_key, origin_address, destination_address):
        """
        Call Google Distance Matrix API and return normalized trip information.

        The method keeps the external API handling isolated from the button
        action so the parsing and error management can be reused or replaced
        later if another distance provider is introduced.
        """
        _logger.info(
            "IK get_google_distance - request origin=%r destination=%r",
            origin_address, destination_address,
        )
        response = requests.get(
            "https://maps.googleapis.com/maps/api/distancematrix/json",
            params={
                "origins": origin_address,
                "destinations": destination_address,
                "key": api_key,
                "units": "metric",
                "language": "fr",
                "region": "fr",
            },
            timeout=15,
        )
        response.raise_for_status()
        result = response.json()
        _logger.info("IK get_google_distance - response status=%s raw=%s", result.get("status"), result)

        if result.get("status") != "OK":
            _logger.warning("IK get_google_distance - Google Maps API error: %s", result.get("status"))
            raise UserError(_("Google Maps API error: %s") % result.get("status"))

        element = result["rows"][0]["elements"][0]
        if element.get("status") != "OK":
            _logger.warning("IK get_google_distance - element status not OK: %s", element.get("status"))
            raise UserError(_("Unable to compute the distance for this trip: %s") % element.get("status"))

        data = {
            "distance_km": element["distance"]["value"] / 1000,
            "origin_address": result["origin_addresses"][0],
            "destination_address": result["destination_addresses"][0],
        }
        _logger.info("IK get_google_distance - parsed data=%s", data)
        return data

    def action_compute_distance(self):
        """
        Compute the trip distance and display it on the wizard without applying it.

        This lets the employee preview the distance before committing, while
        action_apply remains available to compute and apply in a single step
        for those who do not need to check the details first.
        """
        self.ensure_one()
        self._compute_ik_trip_distance()
        _logger.info("IK action_compute_distance - wizard=%s distance=%s", self.id, self.distance)
        return {
            "type": "ir.actions.act_window",
            "name": _("Mileage Trip"),
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_apply(self):
        """
        Compute the trip distance (if not already computed) and apply it on the expense.

        Wizard records are temporary, so all data required for accounting,
        validation and later mileage allowance calculation must be stored on
        the related expense before closing the wizard.
        """
        self.ensure_one()
        self._compute_ik_trip_distance()
        _logger.info("IK action_apply - start wizard=%s distance=%s", self.id, self.distance)

        vals = {
            "ik_vehicle_id": self.vehicle_id.id,
            "ik_origin_address": self._format_ik_trip_address(
                self.origin_type, self._get_ik_trip_address_parts(self.origin_type, self._get_ik_wizard_address_parts("origin"))
            ),
            "ik_destination_address": self._format_ik_trip_address(
                self.destination_type, self._get_ik_trip_address_parts(self.destination_type, self._get_ik_wizard_address_parts("destination"))
            ),
            "ik_google_origin_address": self.google_origin_address,
            "ik_google_destination_address": self.google_destination_address,
            "ik_trip_type": self.trip_type,
            "ik_distance": self.distance,
        }
        _logger.info("IK action_apply - writing on expense=%s vals=%s", self.expense_id.id, vals)
        self.expense_id.write(vals)
        self.expense_id._compute_ik_amount()
        _logger.info(
            "IK action_apply - done expense=%s ik_scale_id=%s price_unit=%s",
            self.expense_id.id, self.expense_id.ik_scale_id, self.expense_id.price_unit,
        )
        return {"type": "ir.actions.act_window_close"}

    @api.onchange("origin_type")
    def _onchange_origin_type(self):
        """Fill the departure address from the employee home or work address when requested."""
        _logger.info(
            "IK onchange_origin_type - type=%s employee=%s",
            self.origin_type, self.employee_id,
        )
        if self.employee_id and self.origin_type == "home":
            parts = self.employee_id._get_ik_home_address_parts()
        elif self.employee_id and self.origin_type == "work":
            parts = self.employee_id._get_ik_work_address_parts()
        else:
            parts = {"street": False}
        self.origin_street = self._format_ik_trip_address(self.origin_type, parts)
        _logger.info("IK onchange_origin_type - resolved parts=%s", parts)

    @api.onchange("destination_type")
    def _onchange_destination_type(self):
        """Fill the arrival address from the employee home or work address when requested."""
        _logger.info(
            "IK onchange_destination_type - type=%s employee=%s",
            self.destination_type, self.employee_id,
        )
        if self.employee_id and self.destination_type == "home":
            parts = self.employee_id._get_ik_home_address_parts()
        elif self.employee_id and self.destination_type == "work":
            parts = self.employee_id._get_ik_work_address_parts()
        else:
            parts = {"street": False}
        self.destination_street = self._format_ik_trip_address(self.destination_type, parts)
        _logger.info("IK onchange_destination_type - resolved parts=%s", parts)
