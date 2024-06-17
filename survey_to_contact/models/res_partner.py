from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Field to link survey user input to res.partner (if a partner is created from survey results)
    generating_survey_user_input_id = fields.Many2one(comodel_name="survey.user_input", store=True)
