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
        partner_vals, question_map = self._prepare_partner_vals(survey_user_input, group_id=0)
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
                raise UserError(f"Une erreur est suvenu lors de la création des contacts a partir de sondages, plus de détails:\n {e}")

        # Create sub-contacts
        sub_contact_groups = self._group_user_input_lines(survey_user_input)
        for group, lines in sub_contact_groups.items():
            if group != 0:  # Skip group 0 (main contact)
                sub_partner_vals, sub_question_map = self._prepare_partner_vals_from_lines(lines)
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
                    try:
                        # Create the sub-partner if it doesn't exist
                        sub_partner = self.env['res.partner'].create(sub_partner_vals)
                        survey_user_input._create_contact_post_process(sub_partner, survey_user_input)
                    except Exception as e:
                        raise UserError(f"Une erreur est suvenu lors de la création des contacts a partir de sondages, plus de détails:\n {e}")

    def _merge_partner(self, survey_user_input):
        """Update the main contact and create sub-contacts if they don't exist based on survey responses."""
        existing_partner = self.partner_id

        # Prepare values to update for the main contact
        lines_with_override = [
            line for line in survey_user_input.user_input_line_ids
            if line.question_id.sub_contact_group == 0 and line.question_id.override_on_merge
        ]
        fields_to_update = self._prepare_values_for_update(lines_with_override)

        try:
            # Write all fields at once for the main contact
            if fields_to_update:
                existing_partner.write(fields_to_update)
        except Exception as e:
            problematic_fields = [field for field in fields_to_update]
            logger.warning(f"Skipping update for fields {problematic_fields} due to error: {e}")

        # Create or update sub-contacts
        sub_contact_groups = self._group_user_input_lines(survey_user_input)
        for group, lines in sub_contact_groups.items():
            if group != 0:  # Skip group 0 (main contact)
                sub_partner_vals, sub_question_map = self._prepare_partner_vals_from_lines(lines)
                sub_partner_vals['parent_id'] = existing_partner.id
                sub_partner_vals['is_company'] = False
                sub_partner_vals.setdefault('name', "Sub contact from survey")

                # Check if the sub-contact already exists using the email
                email = sub_partner_vals.get('email')
                if email:
                    existing_sub_contact = survey_user_input._get_existing_partner(email)
                    if existing_sub_contact:
                        self._update_existing_sub_contact(survey_user_input, existing_sub_contact, sub_partner_vals)
                    else:
                        self._create_new_sub_contact(existing_partner, sub_partner_vals, survey_user_input, sub_question_map)

    def _update_partner_field(self, partner, line):
        """Update a specific field of the partner based on survey response."""
        question = line.question_id

        try:
            if question.override_on_merge:
                # Prepare the values for update
                values_to_update = self._prepare_sub_partner_vals([line])
                partner.write(values_to_update)
            elif not getattr(partner, line.question_id.res_partner_field.name):
                values_to_update = self._prepare_sub_partner_vals([line])
                partner.write(values_to_update)
        except Exception as e:
            logger.warning(f"Skipping question {question.title} for partner {partner.name} due to error: {e}")

    def _update_existing_sub_contact(self, survey_user_input, sub_contact, sub_partner_vals):
        """Update the fields of an existing sub-contact."""
        lines_with_override = [
            line for line in survey_user_input.user_input_line_ids
            if line.question_id.override_on_merge and line.question_id.sub_contact_group != 0
        ]
        values_to_update = self._prepare_values_for_update(lines_with_override)

        try:
            sub_contact.write(values_to_update)
        except Exception as e:
            problematic_fields = [field for field in values_to_update]
            logger.warning(f"Skipping update for fields {problematic_fields} due to error: {e}")

    def _prepare_values_for_update(self, lines):
        """Prepare the values for updating the partner based on the survey responses."""
        return self._prepare_sub_partner_vals(lines)

    def _prepare_partner_vals(self, survey_user_input, group_id):
        """Prepare the values for the main partner or sub-contacts from the survey responses."""
        lines = [line for line in survey_user_input.user_input_line_ids if line.question_id.sub_contact_group == group_id]
        partner_vals = self._prepare_sub_partner_vals(lines)
        question_map = {line.question_id.res_partner_field.name: line.question_id.title for line in lines}
        logger.warning("Question Map --> {}".format(question_map))
        return partner_vals, question_map

    def _prepare_partner_vals_from_lines(self, lines):
        """Prepare the values and question map from the given survey lines."""
        partner_vals = self._prepare_sub_partner_vals(lines)
        question_map = {line.question_id.res_partner_field.name: line.question_id.title for line in lines}
        return partner_vals, question_map

    def _prepare_sub_partner_vals(self, lines):
        """Prepare values for sub-contacts from the given survey responses.
        Extracts partner values from survey responses.
        Handles basic fields, comments and suggestions storing the values in a dictionary."""
        sub_partner_vals = {}
        comment_entries = set()

        for line in lines:
            try:
                field_name = line.question_id.res_partner_field.name
                field_type = line.question_id.res_partner_field.ttype
                answer_type = line.answer_type

                value = None

                # Handle simple_choice
                if answer_type == "simple_choice":
                    if field_type == 'selection':
                        value = self._find_selection_value(line.question_id.res_partner_field, line.suggested_answer_id.value)
                    elif field_type == 'many2one':
                        value = self._find_many2one_value(line.question_id.res_partner_field, line.suggested_answer_id.value)
                    elif field_type == 'many2many':
                        value = self._find_many2many_value(line.question_id.res_partner_field, line.suggested_answer_id.value)
                    elif field_type == 'one2many':
                        value = self._find_one2many_value(line.question_id.res_partner_field, line.suggested_answer_id.value)
                    elif field_type in ['char', 'text']:
                        value = line.suggested_answer_id.value
                    elif field_type == 'html':
                        value1 = line[f"value_{answer_type}"]
                        value = f"<p>{line.question_id.title}: {value1}</p>"

                    logger.info(f"Value for simple_choice: {value}")

                # Handle multiple_choice
                elif answer_type == "multiple_choice":
                    if field_type == 'many2many':
                        value = self._find_many2many_value(line.question_id.res_partner_field, ", ".join([ans.value for ans in line.suggested_answer_ids]))
                    elif field_type == 'one2many':
                        value = self._find_one2many_value(line.question_id.res_partner_field, ", ".join([ans.value for ans in line.suggested_answer_ids]))
                    elif field_type in ['char', 'text']:
                        value = ", ".join([ans.value for ans in line.suggested_answer_ids])
                    elif field_type == 'html':
                        value = "<br/>".join([f"<p>{line.question_id.title}: {ans.value}</p>" for ans in line.suggested_answer_ids])

                    logger.info(f"Value for multiple_choice: {value}")

                # Handle text_box and char_box
                elif answer_type in ["text_box", "char_box"]:
                    if field_type in ['char', 'text']:
                        value = line[f"value_{answer_type}"]
                    elif field_type == 'many2one':
                        value = self._find_many2one_value(line.question_id.res_partner_field, line[f"value_{answer_type}"])
                    elif field_type == 'many2many':
                        value = self._find_many2many_value(line.question_id.res_partner_field, line[f"value_{answer_type}"])
                    elif field_type == 'one2many':
                        value = self._find_one2many_value(line.question_id.res_partner_field, line[f"value_{answer_type}"])
                    elif field_type == 'html':
                        value = f"<p>{line.question_id.title}: {line[f'value_{answer_type}']}</p>"

                    logger.info(f"Value for text_box/char_box: {value}")

                # Handle numerical_box
                elif answer_type == "numerical_box":
                    if field_type == 'float':
                        value = float(line[f"value_{answer_type}"])
                    elif field_type == 'integer':
                        value = int(line[f"value_{answer_type}"])
                    elif field_type in ['char', 'text']:
                        value = str(line[f"value_{answer_type}"])
                    elif field_type == 'html':
                        value = f"<p>{line.question_id.title}: {line[f'value_{answer_type}']}</p>"

                    logger.info(f"Value for numerical_box: {value}")

                # Handle date
                elif answer_type == "date":
                    if field_type == 'date':
                        value = fields.Date.to_date(line[f"value_{answer_type}"])
                    elif field_type in ['char', 'text']:
                        value = str(fields.Date.to_date(line[f"value_{answer_type}"]))
                    elif field_type == 'html':
                        value = f"<p>{line.question_id.title}: {fields.Date.to_date(line[f'value_{answer_type}'])}</p>"

                    logger.info(f"Value for date: {value}")

                # Handle datetime
                elif answer_type == "datetime":
                    if field_type == 'datetime':
                        value = fields.Datetime.to_datetime(line[f"value_{answer_type}"])
                    elif field_type in ['char', 'text']:
                        value = str(fields.Datetime.to_datetime(line[f"value_{answer_type}"]))
                    elif field_type == 'html':
                        value = f"<p>{line.question_id.title}: {fields.Datetime.to_datetime(line[f'value_{answer_type}'])}</p>"

                    logger.info(f"Value for datetime: {value}")

                # Handle suggestions
                elif answer_type == "suggestion":
                    if field_type == 'selection':
                        value = self._find_selection_value(line.question_id.res_partner_field, line.suggested_answer_id.value)
                    elif field_type == 'many2one':
                        value = self._find_many2one_value(line.question_id.res_partner_field, line.suggested_answer_id.value)
                    elif field_type == 'many2many':
                        value = self._find_many2many_value(line.question_id.res_partner_field, line.suggested_answer_id.value)
                    elif field_type == 'one2many':
                        value = self._find_one2many_value(line.question_id.res_partner_field, line.suggested_answer_id.value)
                    elif field_type in ['char', 'text']:
                        value = line.suggested_answer_id.value
                    elif field_type == 'html':
                        value = f"<p>{line.question_id.title}: {line.suggested_answer_id.value}</p>"

                    logger.info(f"Value for suggestion: {value}")

                # Concatenate values
                if value:
                    logger.info(f"Concatenating value for field {field_name}: {value}")
                    if field_name not in sub_partner_vals:
                        sub_partner_vals[field_name] = value
                    else:
                        if field_type == 'many2many':
                            existing_ids = sub_partner_vals[field_name][0][2] if isinstance(sub_partner_vals[field_name], list) and len(sub_partner_vals[field_name][0]) > 2 else []
                            new_ids = value[0][2] if isinstance(value, list) and len(value[0]) > 2 else []
                            combined_ids = list(set(existing_ids + new_ids))
                            sub_partner_vals[field_name] = [(6, 0, combined_ids)]
                        elif field_type == 'one2many':
                            sub_partner_vals[field_name] += value
                        elif field_type == 'html':
                            sub_partner_vals[field_name] += f"<br/>{value}"
                        elif field_type in ['char', 'text']:
                            sub_partner_vals[field_name] += f", {value}"
                        else:
                            sub_partner_vals[field_name] = value

                    logger.warning(f"Subpartner vals  {sub_partner_vals[field_name]}")

            except KeyError as e:
                logger.error(f"KeyError encountered: {e} for line: {line}")
                continue
            except ValueError as e:
                logger.error(f"ValueError encountered: {e}")
                continue

        return sub_partner_vals

    def _find_selection_value(self, field, text_value):
        """Find the correct selection value based on the text input."""
        selection_options = dict(self.env['res.partner'].fields_get(allfields=[field.name])[field.name]['selection'])
        return selection_options.get(text_value, text_value)

    def _find_many2one_value(self, field, text_value):
        """Find the correct many2one value based on the text input."""
        model = self.env[field.relation]
        record = model.search([('name', '=', text_value)], limit=1)
        return record.id if record else False

    def _find_many2many_value(self, field, text_value):
        """Find the correct many2many values based on the text input."""
        model = self.env[field.relation]
        records = model.search([('name', 'in', text_value.split(', '))])
        return [(6, 0, records.ids)] if records else [(5, 0, 0)]

    def _find_one2many_value(self, field, text_value):
        """Find the correct one2many values based on the text input."""
        model = self.env[field.relation]
        records = model.search([('name', 'ilike', text_value)])
        return [(0, 0, {'name': rec.name}) for rec in records]

    def _group_user_input_lines(self, survey_user_input):
        """Group survey responses by sub-contact group, ignoring the main contact group."""
        sub_contact_groups = {}
        for line in survey_user_input.user_input_line_ids:
            group = line.question_id.sub_contact_group
            if group not in sub_contact_groups:
                sub_contact_groups[group] = []
            sub_contact_groups[group].append(line)
        return sub_contact_groups

    def _create_new_sub_contact(self, parent_partner, sub_partner_vals, survey_user_input, question_map):
        """Create a new sub-contact based on survey responses."""
        sub_partner_vals['parent_id'] = parent_partner.id
        sub_partner_vals.setdefault('name', "Sub contact from survey")
        try:
            new_sub_contact = self.env['res.partner'].create(sub_partner_vals)
            survey_user_input._create_contact_post_process(new_sub_contact, survey_user_input)
        except Exception as e:
            raise UserError(f"Une erreur est suvenu lors de la création des contacts a partir de sondages, plus de détails:\n {e}")
