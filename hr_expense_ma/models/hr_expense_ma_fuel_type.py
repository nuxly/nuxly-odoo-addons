from odoo import api, fields, models


class HrExpenseMaFuelType(models.Model):
    _name = "hr.expense.ma.fuel.type"
    _description = "Mileage allowance fuel type"
    _order = "name"

    name = fields.Char(required=True, translate=True)
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

        The name field is translatable, so it is synchronized for every
        installed language using the corresponding translated Fleet selection
        label. Without this, the name would stay frozen in whichever language
        was active when the synchronization ran, instead of following each
        user's own language.
        """
        field = self.env["fleet.vehicle.model"]._fields["default_fuel_type"]
        codes = dict(field._description_selection(self.env)).keys()
        lang_codes = [code for code, _name in self.env["res.lang"].get_installed()]
        for code in codes:
            fuel_type = self.search([("code", "=", code)], limit=1)
            if not fuel_type:
                fuel_type = self.create({"code": code, "name": code})
            for lang_code in lang_codes:
                translated_selection = dict(field._description_selection(self.env(context={"lang": lang_code})))
                fuel_type.with_context(lang=lang_code).name = translated_selection.get(code, code)
