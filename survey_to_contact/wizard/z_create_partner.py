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
        survey_user_input._create_contact_post_process(new_partner, survey_user_input)

        # Create sub contacts
        sub_contact_groups = self._group_user_input_lines(survey_user_input)
        for group, lines in sub_contact_groups.items():
            if group != 0:  # Ignorer the group 0 (main contact)
                sub_partner_vals = self._prepare_sub_partner_vals(lines)
                sub_partner_vals['parent_id'] = new_partner.id
                sub_partner_vals['is_company'] = False
                sub_partner = self.env['res.partner'].create(sub_partner_vals)
                survey_user_input._create_contact_post_process(sub_partner, survey_user_input)
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
        logger.warning("Creating sub contacts")
        sub_partner_vals = {}
        for line in lines:
            field_name = line.question_id.res_partner_field.name
            if field_name:
                logger.warning("Stage 1")
                if line.answer_type != "suggestion" and line.answer_type != "comment":
                    logger.warning("Not a suggestion")
                    if field_name not in sub_partner_vals:
                        sub_partner_vals[field_name] = line[f"value_{line.answer_type}"]
                    else:
                        sub_partner_vals[field_name] += f", {line[f'value_{line.answer_type}']}"
                logger.warning("Stage 2")
                if line.answer_type == "suggestion" and line.suggested_answer_id:
                    logger.warning("Handling suggestion")
                    suggestion_value = line.suggested_answer_id.value
                    logger.warning("Suggestion values: %s", suggestion_value)
                    if field_name not in sub_partner_vals:
                        sub_partner_vals[field_name] = suggestion_value
                    else:
                        sub_partner_vals[field_name] += f", {suggestion_value}"
                logger.warning("Stage 3 -> sub_partner_vals[field_name]: %s", sub_partner_vals.get(field_name))
                if field_name == "comment":
                    comment_value = (
                        line.suggested_answer_id.value
                        if line.answer_type == "suggestion"
                        else line[f"value_{line.answer_type}"]
                    )
                    logger.warning("Handling comment")
                    logger.warning("Comment values: %s", comment_value)
                    sub_partner_vals.setdefault("comment", "")
                    if sub_partner_vals["comment"]:
                        sub_partner_vals["comment"] += f"\n{line.question_id.title}: {comment_value}"
                    else:
                        sub_partner_vals["comment"] = f"{line.question_id.title}: {comment_value}"
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

                if line.answer_type == "suggestion" and line.suggested_answer_id:
                    suggestion_value = line.suggested_answer_id.value
                    if getattr(existing_partner, field_name):
                        existing_value = getattr(existing_partner, field_name)
                        new_value = f"{existing_value}, {suggestion_value}" if existing_value else suggestion_value
                        existing_partner.write({field_name: new_value})
                    else:
                        existing_partner.write({field_name: suggestion_value})

                if field_name == "comment":
                    comment_value = (
                        line.suggested_answer_id.value if line.answer_type == "suggestion" else line[f"value_{line.answer_type}"]
                    )
                    if existing_partner.comment:
                        existing_partner.write({"comment": f"{existing_partner.comment}\n{line.question_id.title}: {comment_value}"})
                    else:
                        existing_partner.write({"comment": f"{line.question_id.title}: {comment_value}"})

        # Update or create sub contacts
        sub_contact_groups = self._group_user_input_lines(survey_user_input)
        for group, lines in sub_contact_groups.items():
            sub_partner_vals = {line.question_id.res_partner_field.name: line[f"value_{line.answer_type}"] for line in lines}
            sub_contact_email = sub_partner_vals.get('email')
            if sub_contact_email:
                existing_sub_contact = self.env['res.partner'].search([
                    ('parent_id', '=', existing_partner.id),
                    ('email', '=', sub_contact_email)
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
