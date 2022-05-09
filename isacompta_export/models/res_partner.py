from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    z_code_client = fields.Char(
        'Code client',
        company_dependent=True,
        help='Compte tiers (client) utilisé en comptabilité. Il sera utilisé pour exporter la comptabilité.')
    z_code_fournisseur = fields.Char(
        'Code fournisseur',
        company_dependent=True,
        help='Compte tiers (fournisseur) utilisé en comptabilité. Il sera utilisé pour exporter la comptabilité.')
