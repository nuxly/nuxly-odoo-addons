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
        domain="[('model', '=', 'res.partner')]",
    )

class SurveyQuestionAnswer(models.Model):
    _inherit = "survey.question.answer"

    res_partner_field = fields.Many2one(
        related="question_id.res_partner_field",
        string="Related Contact Field",
        store=True,
        readonly=False
    )
    res_partner_field_resource_ref = fields.Reference(
        string="Contact Field Value",
        selection="_selection_res_partner_field_resource_ref"
    )

    @api.model
    def _selection_res_partner_field_resource_ref(self):
        """Provide a selection list of models for the reference field."""
        return [(model.model, model.name) for model in self.env["ir.model"].search([])]
