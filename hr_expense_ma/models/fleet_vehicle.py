from odoo import fields, models


class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"

    is_personal_vehicle = fields.Boolean(string="Personal vehicle", tracking=True, help="Enable this option when the vehicle is personally owned by the employee and can be used for mileage allowance expenses.",)
