from odoo import api, fields, models


class HrExpenseMaScale(models.Model):
    _name = "hr.expense.ma.scale"
    _description = "Mileage allowance scale"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "year desc, vehicle_type, fuel_type, horsepower_min, distance_min"

    name = fields.Char(compute="_compute_name", store=True)
    year = fields.Integer(string="Fiscal year", required=True, tracking=True, help="Fiscal year of the official mileage allowance scale. The year is matched with the expense date, not the creation or validation date.")
    vehicle_type = fields.Selection([("car", "Car"), ("motorcycle", "Motorcycle")], string="Vehicle type", required=True, tracking=True, help="Vehicle type covered by this scale line. It must match the vehicle type defined on the Fleet vehicle model.")
    fuel_type = fields.Selection([("thermal_hybrid", "Thermal / Hybrid"), ("electric", "Electric")], string="Fuel type", required=True, tracking=True, help="Fuel category used for the mileage allowance scale. Electric vehicles use the electric scale; all other Fleet fuel types are handled as thermal/hybrid.")
    horsepower_min = fields.Integer(string="Minimum fiscal power", required=True, tracking=True, help="Minimum fiscal power, in CV, covered by this scale line.")
    horsepower_max = fields.Integer(string="Maximum fiscal power", tracking=True, help="Maximum fiscal power, in CV, covered by this scale line. Leave empty for open-ended ranges, such as 7 CV and more.")
    distance_min = fields.Integer(string="Minimum distance", required=True, tracking=True, help="Minimum yearly mileage distance, in kilometers, covered by this scale line.")
    distance_max = fields.Integer(string="Maximum distance", tracking=True, help="Maximum yearly mileage distance, in kilometers, covered by this scale line. Leave empty for open-ended ranges, such as more than 20,000 km.")
    coefficient = fields.Float(string="Coefficient", required=True, digits=(16, 6), tracking=True, help="Multiplier applied to the mileage distance for this scale line.")
    fixed_amount = fields.Float(string="Fixed amount", digits=(16, 2), tracking=True, help="Fixed amount added to the mileage calculation for this scale line.")

    @api.depends("year", "vehicle_type", "fuel_type", "horsepower_min", "horsepower_max", "distance_min", "distance_max")
    def _compute_name(self):
        for scale in self:
            hp = f"{scale.horsepower_min}+" if not scale.horsepower_max else f"{scale.horsepower_min}-{scale.horsepower_max}"
            distance = f"{scale.distance_min}+" if not scale.distance_max else f"{scale.distance_min}-{scale.distance_max}"
            scale.name = f"{scale.year} - {scale.vehicle_type} - {scale.fuel_type} "
