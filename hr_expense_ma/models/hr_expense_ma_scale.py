from odoo import api, fields, models, _


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
        vehicle_type_labels = dict(self._fields["vehicle_type"]._description_selection(self.env))
        for scale in self:
            vehicle_type_label = vehicle_type_labels.get(scale.vehicle_type, scale.vehicle_type)
            if scale.horsepower_max:
                hp = _("%(min)s to %(max)s CV", min=scale.horsepower_min, max=scale.horsepower_max)
            else:
                hp = _("%(min)s CV and above", min=scale.horsepower_min)
            if scale.distance_max:
                distance = _("%(min)s to %(max)s km", min=scale.distance_min, max=scale.distance_max)
            else:
                distance = _("%(min)s km and above", min=scale.distance_min)
            fuel_types = ", ".join(scale.fuel_type_ids.mapped("name")) or "-"
            scale.name = f"{scale.start_date} - {vehicle_type_label} - {fuel_types} - {hp} - {distance}"

    def _compute_amount(self, distance):
        """Compute the yearly mileage allowance amount for a given distance."""
        self.ensure_one()
        return (distance * self.coefficient) + self.fixed_amount
