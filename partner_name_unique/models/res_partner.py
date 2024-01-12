from odoo import fields, api, models
from unidecode import unidecode
import logging
logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Compute fields to find partners with duplicate names
    z_same_name_partner_id = fields.Many2one(
        'res.partner', 
        string='Partner with Same Name', 
        compute='_compute_same_name_partner_id', 
        store=False,
        default=""
    )

    # Compute function that return the same_name_partner if exists
    @api.depends('name', 'company_id', 'company_registry')
    def _compute_same_name_partner_id(self):
        for partner in self:
            # use _origin to deal with onchange()
            partner_id = partner._origin.id
            #active_test = False because if a partner has been deactivated you still want to raise the error,
            #so that you can reactivate it instead of creating a new one, which would loose its history.
            Partner = self.with_context(active_test=False).sudo()

            # Normalize the name for accents and convert to lowercase
            name_normalized = unidecode(partner.name.strip()).lower()
            logger.warning("Nom normalisé 1 {}".format(name_normalized))

            # Prepare the search domain
            domain = []
            if partner.company_id:
                domain += [('company_id', 'in', [False, partner.company_id.id])]
            if partner_id:
                domain += ['!', ('id', 'child_of', partner_id)]

            # Search for all partners
            all_partners = Partner.search(domain)

            # Filter to find a partner with the same normalized name
            partner.z_same_name_partner_id = False
            for p in all_partners:
                if unidecode(p.name.strip()).lower() == name_normalized and p.id != partner_id:
                    logger.warning("Nom normalisé 2 {}".format(unidecode(p.name.strip()).lower()))
                    partner.z_same_name_partner_id = p.id
                    break
