from odoo import api, fields, models


class HrExpenseMaFuelType(models.Model):
    _name = "hr.expense.ma.fuel.type"
    _description = "Mileage allowance fuel type"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True, help="Technical code matching the Fleet vehicle model fuel type selection.")

    _sql_constraints = [
        ("code_unique", "unique(code)", "The fuel type code must be unique."),
    ]

    @api.model
    def sync_from_fleet_selection(self):
        """
        Synchronize mileage allowance fuel types with the Fleet fuel type selection (fleet.vehicle.model)

        The mileage allowance module reuses fuel types defined by Fleet in order to avoid maintaining a separate list. During module installation or
        upgrade, missing fuel types are automatically created and existing ones are updated when their labels change.

        Synchronization is performed using the technical fuel type code to preserve existing relations and avoid duplicate records.
        """
        selection = self.env["fleet.vehicle.model"]._fields["default_fuel_type"].selection
        for code, name in selection:
            fuel_type = self.search([("code", "=", code)], limit=1)
            if fuel_type:
                fuel_type.name = name
            else:
                self.create({"code": code, "name": name})
