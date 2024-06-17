from odoo import models, fields, api
import logging

logger = logging.getLogger(__name__)

class CreatePartnerWizard(models.TransientModel):
    _name = 'z.create.partner.wizard'
    _description = 'Wizard to create or merge partner'

    # Selection field to choose the action to create or merge partner
    action = fields.Selection([
        ('create', 'Create new partner'),
        ('merge', 'Merge with an existing partner')
    ], required=True, string="Action")
    
    partner_id = fields.Many2one('res.partner', string="partner")

    # Perform create or merge action based on the selected option
    def action_create_or_merge(self):
        logger.info("Starting action_create_or_merge")
        survey_user_input = self.env['survey.user_input'].browse(self.env.context.get('default_survey_id'))
        logger.info("Survey user input: %s", survey_user_input)
        
        if self.action == 'create':
            logger.info("Action: Create")
            partner_vals = survey_user_input._prepare_partner()
            logger.info("Prepared partner values: %s", partner_vals)
            partner_vals['is_company'] = True
            
            if not partner_vals.get('name'):
                logger.error("The name field is missing. Setting default name to 'Unnamed Partner'.")
                partner_vals['name'] = "Contact from survey"
                
            new_partner = self.env['res.partner'].create(partner_vals)
            logger.info("New partner created: %s", new_partner)
            survey_user_input._create_contact_post_process(new_partner)
            logger.info("Post-process completed for new partner.")
        
        elif self.action == 'merge':
            logger.info("Action: Merge")
            existing_partner = self.partner_id
            logger.info("Existing partner: %s", existing_partner)
            # partner_vals = self._prepare_partner_from_survey(survey_user_input)
            partner_vals = survey_user_input._prepare_partner()
            logger.info("Prepared partner values: %s", partner_vals)
            
            if not partner_vals.get('name'):
                partner_vals['name'] = existing_partner.name
            
            existing_partner.write(partner_vals)
            logger.info("Existing partner updated: %s", existing_partner)
