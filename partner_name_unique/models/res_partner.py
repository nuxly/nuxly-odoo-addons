from odoo import fields, api, models
from unidecode import unidecode

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
    @api.depends('name', 'company_id')
    def _compute_same_name_partner_id(self):
        for partner in self:
            # use _origin to deal with onchange()
            partner_id = partner._origin.id
            #active_test = False because if a partner has been deactivated you still want to raise the error,
            #so that you can reactivate it instead of creating a new one, which would loose its history.
            Partner = self.with_context(active_test=False).sudo()
            if partner.name:
                #add specific standards for names to take into specific accents and lower upper letters
                name_normalized = unidecode(partner.name.strip().lower())
                domain = [
                    ('name', '=', name_normalized),
                ]
                if partner.company_id:
                    domain += [('company_id', 'in', [False, partner.company_id.id])]
                if partner_id:
                    domain += ['!', ('id', 'child_of', partner_id)]
                partner.z_same_name_partner_id = not partner.parent_id and Partner.search(domain, limit=1)
