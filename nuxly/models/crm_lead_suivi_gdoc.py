import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class crmLeadSuiviGDoc(models.Model):
    _inherit = 'crm.lead'
    gdoc_url = fields.Char(string="Suivi GDoc", translate=True, required=False, help='Lien du suivi Google Doc')
