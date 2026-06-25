from odoo import api, fields, models


class HrExpenseMaScale(models.Model):
    _name = "hr.expense.ma.scale"
    _description = "Mileage allowance scale"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "start_date desc, vehicle_type, horsepower_min, distance_min"

    name = fields.Char(compute="_compute_name", store=True)
    start_date = fields.Date(string="Start date", required=True, tracking=True, help="Start date of the official mileage allowance scale. During calculation, the latest scale with a start date lower than or equal to the expense date will be used.")    
    vehicle_type = fields.Selection([("car", "Car"), ("motorcycle", "Motorcycle")], string="Vehicle type", required=True, tracking=True, help="Vehicle type covered by this scale line. It must match the vehicle type defined on the Fleet vehicle model.")
    fuel_type_ids = fields.Many2many("hr.expense.ma.fuel.type", string="Fuel types", tracking=True, help="Fleet fuel types covered by this scale line. Values are synchronized from the Fleet vehicle model fuel type selection.")    
    horsepower_min = fields.Integer(string="Minimum fiscal power", required=True, tracking=True, help="Minimum fiscal power, in CV, covered by this scale line.")
    horsepower_max = fields.Integer(string="Maximum fiscal power", tracking=True, help="Maximum fiscal power, in CV, covered by this scale line. Leave empty for open-ended ranges, such as 7 CV and more.")
    distance_min = fields.Integer(string="Minimum distance", required=True, tracking=True, help="Minimum yearly mileage distance, in kilometers, covered by this scale line.")
    distance_max = fields.Integer(string="Maximum distance", tracking=True, help="Maximum yearly mileage distance, in kilometers, covered by this scale line. Leave empty for open-ended ranges, such as more than 20,000 km.")
    coefficient = fields.Float(string="Coefficient", required=True, digits=(16, 6), tracking=True, help="Multiplier applied to the mileage distance for this scale line.")
    fixed_amount = fields.Float(string="Fixed amount", digits=(16, 2), tracking=True, help="Fixed amount added to the mileage calculation for this scale line.")

    @api.depends("start_date", "vehicle_type", "fuel_type_ids", "horsepower_min", "horsepower_max", "distance_min", "distance_max")
    def _compute_name(self):
        # Compute the display name of the mileage allowance scale.
        for scale in self:
            hp = f"{scale.horsepower_min}+" if not scale.horsepower_max else f"{scale.horsepower_min}-{scale.horsepower_max}"
            distance = f"{scale.distance_min}+" if not scale.distance_max else f"{scale.distance_min}-{scale.distance_max}"
            fuel_types = ", ".join(scale.fuel_type_ids.mapped("name")) or "-"
            scale.name = f"{scale.start_date} - {scale.vehicle_type} - {fuel_types} - {hp} CV - {distance} km"
