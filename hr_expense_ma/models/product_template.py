from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_ik_expense = fields.Boolean(string="Mileage allowance", tracking=True, help="Enable this option to identify this expense product as a mileage allowance product.",)