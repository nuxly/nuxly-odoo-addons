import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class crm_lead(models.Model):
    _inherit = 'crm.lead'
    category_id = fields.Char(string="Suivi GDoc", translate=True, required=False, help='Lien du suivi Google Doc')
