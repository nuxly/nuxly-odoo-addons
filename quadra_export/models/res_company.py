from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    expc_testing = fields.Boolean(
        'Enabled testing mode for Quadra export',
        help="Enable the 'testing' mode for the Quadra export : The lines will not be affected by the exportation.",
    )
