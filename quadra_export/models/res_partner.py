from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    quadra_customer_code = fields.Char(
        'Customer code',
        company_dependant=True,
        help='Customer third-party account used in accounting. It will be used for export.')
    quadra_supplier_code = fields.Char(
        'Provider code',
        company_dependant=True,
        help='Provider third-party account used in accounting. It will be used for export.')