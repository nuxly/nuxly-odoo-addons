from datetime import datetime, date
import logging
from odoo import models

_logger = logging.getLogger(__name__)


class TimesheetReminder(models.TransientModel):
    _name = 'timesheet.reminder'
    _description = "Alert each user who hasn't provided at least one timesheet line and that is not in vacation"

    # Checks that their timesheet lines have been correctly entered by the users
    def _cron_timesheet_reminder(self):
        holidays_public_line = self.env['hr.holidays.public.line']
        leave = self.env['hr.leave']
        timesheet_line = self.env['account.analytic.line']
        hr_employee = self.env['hr.employee']

        today = date.today()
        today_time = datetime.now()

        _logger.info("Starting the check of employee timesheet lines...")
        # Checks if the day is a working day
        if today.weekday() in [0, 1, 2, 3, 4]:
            # Checks if the day is not a public holiday
            holiday = holidays_public_line.search([]).filtered(lambda x: x.date == today)
            if not holiday:
                # Retrieves only employees who must write at least one timesheet line
                employees = hr_employee.search([('ignore_timesheet_reminder', '=', False)])
                for employee in employees:
                    _logger.info("Check for '%s'.", employee.name)
                    # Checks if the employee is not on leave
                    on_leave = leave.search([('employee_id', '=', employee.id)]).filtered(
                        lambda x: x.number_of_days == 1.0 and x.date_from == today_time or x.date_from <= today_time <= x.date_to)
                    if not on_leave:
                        # Checks if the employee has written at least one timesheet line
                        lines = timesheet_line.search([('date', '=', today), ('employee_id', '=', employee.id)])
                        if not lines:
                            # Preparing the reminder email
                            self._send_timesheet_reminder(
                                employee,
                                'reminder_summary_timesheet.reminder_timesheet_fill',
                                'hr_timesheet.act_hr_timesheet_line'
                            )
        _logger.info("End of check.")

    # Send an email timesheet line entry reminder to specified users
    def _send_timesheet_reminder(self, employees, template_xmlid, action_xmlid, additionnal_values=None):
        action_url = '%s/web#menu_id=%s&action=%s' % (
            self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
            self.env.ref('hr_timesheet.timesheet_menu_root').id,
            self.env.ref(action_xmlid).id,
        )
        template = self.env.ref(template_xmlid)
        template_ctx = {'action_url': action_url}
        if additionnal_values:
            template_ctx.update(additionnal_values)
        for employee in employees:
            template.with_context(**template_ctx).send_mail(employee.id)
            _logger.info("A timesheet line entry reminder has been sent to '%s'.", employee.name)
