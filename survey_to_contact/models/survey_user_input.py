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

    # Send an internal message with the input link af survey and responsesafter creating the partner
    def _create_contact_post_process(self, partner, survey_user_input, edit=False):
        """After creating the contact, send an internal message with the input link of survey."""
        object_name = self.env['ir.model']._get(self._name).name.lower()
        partner.message_post_with_view(
            "survey_to_contact.z_message_survey_creat_edit",
            values={
                "self": partner,
                "origin1": [self.survey_id],  
                "origin2": [survey_user_input],
                "edit": edit,
                "object_name": object_name
            },
            subtype_id=self.env.ref("mail.mt_note").id,
        )

    def _get_existing_partner(self, email, limit=1):
        """Hook method that can be used to change the behavior of contact generation"""
        return self.env["res.partner"].search([("email", "=ilike", email)], limit=limit)