from odoo import models, fields

class SurveySurvey(models.Model):
    _inherit = 'survey.survey'

    # Boolean to enable the creation of contacts from surveys
    z_show_create_partner_button = fields.Boolean(string="Show create partner button", default=False)

    # Boolean to determine if a parent contact should be created
    create_parent_contact = fields.Boolean(
        help="Set the company_name in a question and a parent contact will be "
        "created to hold the generated one",
        default=True
    )