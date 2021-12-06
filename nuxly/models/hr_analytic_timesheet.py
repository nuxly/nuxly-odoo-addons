# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class hr_analytic_timesheet(models.Model):
    _inherit = 'account.analytic.line'

    def _getDefaultUnit(self):
        return self.env['uom.uom'].with_context(lang='fr_FR').search([('name', '=', 'Jour(s)')], limit=1) or False

    time_spend = fields.Float('Temps passé', required=True, help='Temps passé')
    unit_time_spend = fields.Many2one('uom.uom', 'Unité', required=True, help='Unité de mesure de temps de facturation',
                                      default=_getDefaultUnit)
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('to_check', 'A Valider'),
        ('checked', 'Validé'),
        ('closed', 'Clôturé'),
    ], default='to_check', string='Etat', required=True, help='Etat')

    # TODO Charge la valeur pas defaut à heure
    # @api.model
    # def _getDefaultUnit(self):
    # return self.env['uom.uom'].with_context(lang='en_US').search([('name', '=', 'Hour(s)')], limit=1) or False

    # Calcul de temps à facturé en fonction du temps passé et de l'article du projet
    @api.onchange('time_spend')
    def on_change_time_spend(self):
        _logger.info("on_change_time_spend starting ...")
        #if not self.account_id:
            #return
        # Si le projet est en facturation sur le temps
        if self.project_id.timesheet_encode_uom_id:
            _logger.info("convert will started : ")
            self.unit_amount = self.convertTime(self.time_spend, self.encoding_uom_id, self.unit_time_spend)
        _logger.info("méthode on_change_time_spend ending ...")

    def convertTime(self, time, inUnit, outUnit):
        _logger.info(inUnit.category_id)
        _logger.info(outUnit.category_id)
        if inUnit.category_id != outUnit.category_id:
            raise UserError("Les deux unités ne sont pas compatibles")

        # Si l'unité est la meme en entre que en sortie, pas de conversion
        if inUnit.name == outUnit.name:
            return time
        # Convertir d'heure en jour
        # TODO : bug si changement de langue
        _logger.info(inUnit.name)
        _logger.info(outUnit.name)

        # if inUnit.name == "Heure(s)" and outUnit.name == "Jour(s)":
        if inUnit.name == "Heure(s)" and outUnit.name == "Jour(s)":
            if time < 1.0:
                return time / 5.0
            elif time > 6.0:
                return 1
            else:
                return time / 6.0
        else:
            raise UserError("Conversion non gérée")

    def wizard_show_state(self):
        return {
            'name': 'Changer l\'état',
            'view_mode': 'form',
            'res_model': 'global.timesheet.state',
            'views': [(self.env.ref('nuxly.wizard_global_timesheet_state').id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': dict(self.env.context, active_ids=self.ids),
        }

    def event_delete(self):
        _logger.info(self.id)
        return {
            'name': 'change l\'état',
            'view_mode': 'form',
            'res_model': 'global.timesheet.state',
            'views': [(self.env.ref('nuxly.delete_timesheet_line_confirm_view').id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': dict(self.env.context, active_id=self.id),
        }
