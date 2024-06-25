from odoo import models, fields

class SurveySurvey(models.Model):
    _inherit = 'survey.survey'

    # Boolean to enable the creation of contacts from surveys
    z_show_create_partner_button = fields.Boolean(string="Show create partner button", default=False)
