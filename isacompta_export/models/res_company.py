from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    expc_testing = fields.Boolean(
        'Enabled testing mode for Isacompta export',
        help="Enable the 'testing' mode for the Isacompta export : The lines will not be affected by the exportation.",
    )
