from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    is_ik_expense = fields.Boolean(string="Mileage allowance", tracking=True, help="Enable this option to identify this product as a mileage allowance expense.")