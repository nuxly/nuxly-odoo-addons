from odoo import models, fields, api
from odoo.exceptions import UserError
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

    def action_create_or_merge(self):
        """Execute the selected action to either create a new partner or merge with an existing partner."""
        survey_user_input = self.env['survey.user_input'].browse(self.env.context.get('default_survey_id'))

        if self.action == 'create':
            self._create_partner(survey_user_input)
        elif self.action == 'merge':
            self._merge_partner(survey_user_input)

    def _create_partner(self, survey_user_input):
        """Create the main partner and sub-contacts from survey responses."""
        partner_vals = self._prepare_partner_vals(survey_user_input, group_id=0)
        partner_vals['is_company'] = True
        partner_vals.setdefault('name', "Contact from survey")

        # Check if the main contact already exists using the hook method
        existing_partner = survey_user_input._get_existing_partner(partner_vals.get('email'))
        if existing_partner:
            new_partner = existing_partner
        else:
            try:
                # Create the main partner if it doesn't exist
                new_partner = self.env['res.partner'].create(partner_vals)
                new_partner.write({'is_company': True})
                survey_user_input._create_contact_post_process(new_partner, survey_user_input)
            except Exception as e:
                new_partner = None # If values not correct
                user_message = "An error occurred while creating the contact. Please check the field values or ensure that the responses match the expected types."
                raise UserError(user_message)
        # Create sub-contacts
        sub_contact_groups = self._group_user_input_lines(survey_user_input)
        for group, lines in sub_contact_groups.items():
            if group != 0:  # Skip group 0 (main contact)
                sub_partner_vals = self._prepare_sub_partner_vals(lines)
                sub_partner_vals['parent_id'] = new_partner.id
                sub_partner_vals['is_company'] = False
                sub_partner_vals.setdefault('name', "Sub contact from survey")

                # Check if the sub-contact already exists
                existing_sub_contact = None
                email = sub_partner_vals.get('email')
                if email:
                    existing_sub_contact = survey_user_input._get_existing_partner(email)
                if existing_sub_contact:
                    sub_partner = existing_sub_contact
                else:
                    # Create the sub-partner if it doesn't exist
                    sub_partner = self.env['res.partner'].create(sub_partner_vals)
                    survey_user_input._create_contact_post_process(sub_partner, survey_user_input)

    def _merge_partner(self, survey_user_input):
        """Update the main contact and create sub-contacts if they don't exist based on survey responses."""
        existing_partner = self.partner_id

        # Update main contact
        for line in survey_user_input.user_input_line_ids:
            if line.answer_type and line.question_id.sub_contact_group == 0 and line.question_id.res_partner_field:
                self._update_partner_field(existing_partner, line)


        # Create or update sub-contacts
        sub_contact_groups = self._group_user_input_lines(survey_user_input)
        for group, lines in sub_contact_groups.items():
            if group != 0:  # Skip group 0 (main contact)
                sub_partner_vals = self._prepare_sub_partner_vals(lines)
                sub_partner_vals['parent_id'] = existing_partner.id
                sub_partner_vals['is_company'] = False
                sub_partner_vals.setdefault('name', "Sub contact from survey")

                # Check if the sub-contact already exists using the email
                if sub_partner_vals.get('email'):
                    existing_sub_contact = survey_user_input._get_existing_partner(sub_partner_vals.get('email'))
                    if not existing_sub_contact:
                        self._create_new_sub_contact(existing_partner, sub_partner_vals, survey_user_input)
                else:
                    self._create_new_sub_contact(existing_partner, sub_partner_vals, survey_user_input)
                
    def _update_partner_field(self, partner, line):
        """Update a specific field of the partner based on survey response."""
        field_name = line.question_id.res_partner_field.name
        value = line.suggested_answer_id.value if line.answer_type == "suggestion" else line[f"value_{line.answer_type}"]
        question = line.question_id
        if question.override_on_merge:
            partner.write({field_name: value})
        elif not getattr(partner, field_name):
            partner.write({field_name: value})

    def _prepare_partner_vals(self, survey_user_input, group_id):
        """Prepare the values for the main partner or sub-contacts from the survey responses."""
        lines = [line for line in survey_user_input.user_input_line_ids if line.question_id.sub_contact_group == group_id]
        return self._prepare_sub_partner_vals(lines)

    def _prepare_sub_partner_vals(self, lines):
        """Prepare values for sub-contacts from the given survey responses.
           Extracts partner values from survey responses.
           Handles basic fields, comments and suggestions storing the values in a dictionary."""
        sub_partner_vals = {}
        comment_entries = set()
        for line in lines:
            try:
                field_name = line.question_id.res_partner_field.name
                if field_name and line.answer_type:
                    if line.answer_type != "suggestion" and line.answer_type != "comment":
                        value = line[f"value_{line.answer_type}"]
                        if field_name not in sub_partner_vals:
                            sub_partner_vals[field_name] = value
                        else:
                            sub_partner_vals[field_name] += f", {value}"
                    if line.answer_type == "suggestion" and line.suggested_answer_id:
                        suggestion_value = line.suggested_answer_id.value
                        if field_name != "comment":
                            if field_name not in sub_partner_vals:
                                sub_partner_vals[field_name] = f"<br>{line.question_id.title}: {suggestion_value}<br>"
                            else:
                                sub_partner_vals[field_name] += f"<br>{line.question_id.title}: {suggestion_value}<br>"
                    if field_name == "comment":
                        comment_value = (
                            line.suggested_answer_id.value
                            if line.answer_type == "suggestion"
                            else line[f"value_{line.answer_type}"]
                        )
                        comment_entry = f"<br>{line.question_id.title}: {comment_value}<br>"
                        if comment_entry not in comment_entries:
                            comment_entries.add(comment_entry)
                            sub_partner_vals.setdefault("comment", "")
                            sub_partner_vals["comment"] += comment_entry
            except ValueError as e:
                continue
        return sub_partner_vals

    def _group_user_input_lines(self, survey_user_input):
        """Group survey responses by sub-contact group, ignoring the main contact group."""
        sub_contact_groups = {}
        for line in survey_user_input.user_input_line_ids:
            group = line.question_id.sub_contact_group
            if group not in sub_contact_groups:
                sub_contact_groups[group] = []
            sub_contact_groups[group].append(line)
        return sub_contact_groups

    def _update_existing_sub_contact(self, sub_contact, sub_partner_vals):
        """Update the fields of an existing sub-contact."""
        for field, value in sub_partner_vals.items():
            question = self.env['survey.question'].search([('res_partner_field.name', '=', field)], limit=1)
            if question and question.override_on_merge:
                sub_contact.write({field: value})
            elif not getattr(sub_contact, field):
                sub_contact.write({field: value})

    def _create_new_sub_contact(self, parent_partner, sub_partner_vals, survey_user_input):
        """Create a new sub-contact based on survey responses."""
        sub_partner_vals['parent_id'] = parent_partner.id
        sub_partner_vals.setdefault('name', "Sub contact from survey")
        new_sub_contact = self.env['res.partner'].create(sub_partner_vals)
        survey_user_input._create_contact_post_process(new_sub_contact, survey_user_input)
