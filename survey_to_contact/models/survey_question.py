from odoo import api, fields, models

class SurveyQuestion(models.Model):
    _inherit = "survey.question"

    override_on_merge = fields.Boolean(
        string="Override on merge?",
        help="If checked, this field's value will overwrite the existing value during the merge.",
        default=False
    )
    sub_contact_group = fields.Integer(
        string="Sub contact group",
        help="Indicates the group number for sub-contacts. Used to create child contacts under the main contact."
    )
    res_partner_field = fields.Many2one(
        string="Contact field",
        comodel_name="ir.model.fields",
        domain="[('model', '=', 'res.partner'), ('store', 'in', [True, False])]",
    )