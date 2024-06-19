from odoo import models, fields, api
import logging

logger = logging.getLogger(__name__)

class CreatePartnerWizard(models.TransientModel):
    _name = 'z.create.partner.wizard'
    _description = 'Wizard to create or merge partner'

    action = fields.Selection([
        ('create', 'Create new partner'),
        ('merge', 'Merge with an existing partner')
    ], required=True, string="Action")

    partner_id = fields.Many2one('res.partner', string="Partner")

    # Action create a new partner or merge with an existing one.
    def action_create_or_merge(self):
        logger.info("Starting action_create_or_merge")
        survey_user_input = self.env['survey.user_input'].browse(self.env.context.get('default_survey_id'))
        logger.info("Survey user input: %s", survey_user_input)

        if self.action == 'create':
            self._create_partner(survey_user_input)
        elif self.action == 'merge':
            self._merge_partner(survey_user_input)

    # Creates the main contact and sub-contacts from survey responses.
    def _create_partner(self, survey_user_input):
        partner_vals = self._prepare_sub_partner_vals(
            [line for line in survey_user_input.user_input_line_ids if line.question_id.sub_contact_group == 0]
        )
        partner_vals['is_company'] = True
        if not partner_vals.get('name'):
            partner_vals['name'] = "Contact from survey"

        # Create main contact
        new_partner = self.env['res.partner'].create(partner_vals)
        logger.info("New partner created: %s", new_partner)
        survey_user_input._create_contact_post_process(new_partner)

        # Create sub contacts
        sub_contact_groups = self._group_user_input_lines(survey_user_input)
        for group, lines in sub_contact_groups.items():
            if group != 0:  # Ignorer the group 0 (main contact)
                sub_partner_vals = self._prepare_sub_partner_vals(lines)
                sub_partner_vals['parent_id'] = new_partner.id
                sub_partner_vals['is_company'] = False
                sub_partner = self.env['res.partner'].create(sub_partner_vals)
                logger.info("Sub partner created for group %s: %s", group, sub_partner)

    # Groups survey responses by sub-contact group, ignoring the main contact group.
    def _group_user_input_lines(self, survey_user_input):
        sub_contact_groups = {}
        for line in survey_user_input.user_input_line_ids:
            group = line.question_id.sub_contact_group
            if group != 0:
                if group not in sub_contact_groups:
                    sub_contact_groups[group] = []
                sub_contact_groups[group].append(line)
        return sub_contact_groups

    # Prepares values for sub-contacts from the given survey responses.
    def _prepare_sub_partner_vals(self, lines):
        sub_partner_vals = {}
        for line in lines:
            field_name = line.question_id.res_partner_field.name
            if field_name:
                sub_partner_vals[field_name] = line[f"value_{line.answer_type}"]
        return sub_partner_vals

    # Updates the main contact and sub-contacts based on survey responses, respecting the override_on_merge setting.
    def _merge_partner(self, survey_user_input):
        existing_partner = self.partner_id

        # Update main contact
        for line in survey_user_input.user_input_line_ids:
            if line.question_id.sub_contact_group == 0 and line.question_id.res_partner_field:
                field_name = line.question_id.res_partner_field.name
                value = line[f"value_{line.answer_type}"]
                question = line.question_id
                if question.override_on_merge:
                    existing_partner.write({field_name: value})
                elif not getattr(existing_partner, field_name):
                    existing_partner.write({field_name: value})

        # Update or create sub contact
        sub_contact_groups = self._group_user_input_lines(survey_user_input)
        for group, lines in sub_contact_groups.items():
            sub_partner_vals = {line.question_id.res_partner_field.name: line[f"value_{line.answer_type}"] for line in lines}
            sub_contact_name = sub_partner_vals.get('name')
            if sub_contact_name:
                existing_sub_contact = self.env['res.partner'].search([
                    ('parent_id', '=', existing_partner.id),
                    ('name', '=', sub_contact_name)
                ], limit=1)
                if existing_sub_contact:
                    for field, value in sub_partner_vals.items():
                        question = self.env['survey.question'].search([('res_partner_field.name', '=', field)], limit=1)
                        if question and question.override_on_merge:
                            existing_sub_contact.write({field: value})
                        elif not getattr(existing_sub_contact, field):
                            existing_sub_contact.write({field: value})
                else:
                    sub_partner_vals['parent_id'] = existing_partner.id
                    self.env['res.partner'].create(sub_partner_vals)
