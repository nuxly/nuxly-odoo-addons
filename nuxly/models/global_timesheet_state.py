import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class global_timesheet_state(models.TransientModel):
    _name = 'global.timesheet.state'
    _description = 'Change lz status pour toutes les enregistrements de temps sélectionnées'

    # time_new_state = fields.Many2one("hr.analytic.timesheet.state", "Nouvelle état", required=True, help='Nouvelle
    # état dans lequelle placer les temps séléctionnés')
    time_new_state = fields.Selection([
        ('draft', 'Brouillon'),
        ('to_check', 'AValider'),
        ('checked', 'Validé'),
        ('closed', 'Clôturé'),
    ], default='checked', string='Nouveau statut')

    def wizard_change_state(self):
        obj_timesheet = self.env['account.analytic.line']
        active_ids = self.env.context.get("active_ids")

        for id in active_ids:
            _logger.info("self.time_new_state %s" % self.time_new_state)
            obj_timesheet.browse([id]).write({
                'state': self.time_new_state
            })

        return {'type': 'ir.actions.act_window_close'}

    def confirm_delete(self):
        obj_timesheet = self.env['account.analytic.line']
        active_id = self.env.context.get("active_id")
        _logger.info("test")
        _logger.info(self)
        _logger.info(active_id)
        obj_timesheet.search([('id', '=', active_id)]).unlink()
        return {}
