from odoo import models, fields

class Survey(models.Model):
    _inherit = 'survey.user_input'

    
    survey_id = fields.Many2one('survey.survey', string="Survey", required=True)
    z_show_create_partner_button = fields.Boolean('survey.survey')
    # Boolean to filter if the survey can be converted to a partner
    z_it_can_be_partner = fields.Boolean(string="", help="Filter if the survey can be convert to a partner", related='survey_id.z_show_create_partner_button')

    # Open a wizard to create or merge a partner
    def action_create_partner(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create or merge partner',
            'res_model': 'z.create.partner.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_survey_id': self.id},
        }

    # Prepare partner values from survey answers
    def _prepare_partner(self):
        """Extract partner values from the answers"""
        self.ensure_one()
        elegible_inputs = self.user_input_line_ids.filtered(
            lambda x: x.question_id.res_partner_field and not x.skipped
        )
        basic_inputs = elegible_inputs.filtered(
            lambda x: x.answer_type not in {"suggestion"}
            and x.question_id.res_partner_field.name not in {"comment", "company_name"}
        )
        vals = {
            line.question_id.res_partner_field.name: line[f"value_{line.answer_type}"]
            for line in basic_inputs
        }
        for line in elegible_inputs - basic_inputs:
            field_name = line.question_id.res_partner_field.name
            if line.question_id.res_partner_field.ttype == "many2one":
                vals[
                    field_name
                ] = line.suggested_answer_id.res_partner_field_resource_ref.id
            elif line.question_id.res_partner_field.ttype == "many2many":
                vals.setdefault(field_name, [])
                vals[field_name] += [
                    (4, line.suggested_answer_id.res_partner_field_resource_ref.id)
                ]
            # We'll use the comment field to add any other infos
            elif field_name == "comment":
                vals.setdefault("comment", "")
                value = (
                    line.suggested_answer_id.value
                    if line.answer_type == "suggestion"
                    else line[f"value_{line.answer_type}"]
                )
                vals["comment"] += f"\n{line.question_id.title}: {value}"
            # Create the parent company
            elif field_name == "company_name":
                if line[f"value_{line.answer_type}"]:
                    vals["parent_id"] = (
                        self.env["res.partner"]
                        .create(
                            {
                                "name": line[f"value_{line.answer_type}"],
                                "company_type": "company",
                            }
                        )
                        .id
                    )
            else:
                if line.question_id.question_type == "multiple_choice":
                    if not vals.get(field_name):
                        vals[field_name] = line.suggested_answer_id.value
                    else:
                        vals[field_name] += line.suggested_answer_id.value
                else:
                    vals[field_name] = line.suggested_answer_id.value
        vals["generating_survey_user_input_id"] = self.id
        return vals

    # Send an internal message with the input link after creating the partner
    def _create_contact_post_process(self, partner):
        """After creating the lead send an internal message with the input link"""
        partner.message_post_with_view(
            "mail.message_origin_link",
            values={"self": partner,
                    "origin": self.survey_id},
            subtype_id=self.env.ref("mail.mt_note").id,
        )

    def _get_existing_partner(self, email, limit=1):
        """Hook method that can be used to change the behavior of contact generation"""
        return self.env["res.partner"].search([("email", "=ilike", email)], limit=limit)