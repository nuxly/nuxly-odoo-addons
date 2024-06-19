from odoo import api, fields, models

class SurveyQuestion(models.Model):
    _inherit = "survey.question"

    override_on_merge = fields.Boolean(string="Override on merge?", help="If checked, this field's value will overwrite the existing value during the merge.", default=False)
    sub_contact_group = fields.Integer(string="Sub contact group", help="Indicates the group number for sub-contacts. Used to create child contacts under the main contact.")
    # Allowed fields for the question based on its type
    allowed_field_ids = fields.Many2many(
        comodel_name="ir.model.fields",
        compute="_compute_allowed_field_ids",
    )
    # Contact field to map survey responses to res.partner fields
    res_partner_field = fields.Many2one(
        string="Contact field",
        comodel_name="ir.model.fields",
        domain="[('id', 'in', allowed_field_ids)]",
    )

    # Compute allowed fields based on the question type
    @api.depends("question_type")
    def _compute_allowed_field_ids(self):
        type_mapping = {
            "char_box": ["char", "text"],
            "text_box": ["html"],
            "numerical_box": ["integer", "float", "html", "char"],
            "date": ["date", "text", "char"],
            "datetime": ["datetime", "html", "char"],
            "simple_choice": ["many2one", "html", "char"],
            "multiple_choice": ["many2many", "html", "char"],
        }
        for record in self:
            record.allowed_field_ids = (
                self.env["ir.model.fields"]
                .search(
                    [
                        ("model", "=", "res.partner"),
                        ("ttype", "in", type_mapping.get(record.question_type, [])),
                    ]
                )
                .ids
            )

class SurveyQuestionAnswer(models.Model):
    _inherit = "survey.question.answer"

    @api.model
    def default_get(self, fields):
        # Override to set default values for related partner fields
        result = super().default_get(fields)
        if (
            not result.get("res_partner_field")
            or "res_partner_field_resource_ref" not in fields
        ):
            return result
        partner_field = self.env["ir.model.fields"].browse(result["res_partner_field"])
        # Use the value directly for simple fields (char, text)
        if partner_field.ttype not in {"many2one", "many2many"}:
            return result
        res = self.env[partner_field.relation].search([], limit=1)
        if res:
            result["res_partner_field_resource_ref"] = "%s,%s" % (
                partner_field.relation,
                res.id,
            )
        return result

    @api.model
    def _selection_res_partner_field_resource_ref(self):
        # Selection list of models for the reference field
        return [(model.model, model.name) for model in self.env["ir.model"].search([])]
    # Related field to res.partner field selected in the survey question
    res_partner_field = fields.Many2one(related="question_id.res_partner_field")
    res_partner_field_resource_ref = fields.Reference(
        string="Contact field value",
        selection="_selection_res_partner_field_resource_ref",
    )

    @api.onchange("res_partner_field_resource_ref")
    def _onchange_res_partner_field_resource_ref(self):
        """Set the default value as the product name, although we can change it"""
        if self.res_partner_field_resource_ref:
            self.value = self.res_partner_field_resource_ref.display_name or ""
