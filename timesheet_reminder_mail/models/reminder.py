from datetime import datetime, date
import logging
from odoo import models

_logger = logging.getLogger(__name__)


class Reminder(models.TransientModel):
    _name = 'timesheet.reminder'
    _description = "Alert each user that doesn't wrote at least one line of time on timesheet"

    def _cron_reminder(self):
        public_holiday = self.env['hr.holidays.public.line']
        leave = self.env['hr.leave']
        timesheet = self.env['account.analytic.line']
        hr_employee = self.env['hr.employee']

        today = date.today()
        today_time = datetime.now()

        # Checking working day (not weekend)
        if today.weekday() in [0, 1, 2, 3, 4]:
            # checking if day is a holiday
            holiday = public_holiday.search([]).filtered(lambda x: x.date == today)
            if not holiday:
                # Check for all employees, if each one write at least one line of timesheet
                employees = hr_employee.search([])
                for employee in employees:
                    # Check if each one doesn't on leave
                    on_leave = leave.search([('employee_id', '=', employee.id)]).filtered(lambda
                                                                                             x: x.number_of_days == 1.0 and x.date_from == today_time or x.date_from <= today_time <= x.date_to)
                    if not on_leave:
                        # Check if each one write at least one line of timesheet, or do a alert
                        lines = timesheet.search([('date', '=', today), ('employee_id', '=', employee.id)])
                        if not lines:
                            self._cron_timesheet_send_reminder(
                                employee,
                                'timesheet_reminder_mail.reminder_timesheet_fill',
                                'hr.open_view_employee_list_my'
                            )

    def _cron_timesheet_send_reminder(self, employees, template_xmlid, action_xmlid, additionnal_values=None):
        """ Send the email reminder to specified users
            :param user_ids : list of user identifier to send the reminder
            :param template_xmlid : xml id of the reminder mail template
        """
        action_url = '%s/web#menu_id=%s&action=%s' % (
            self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
            self.env.ref('hr.open_view_employee_list_my').id,
            self.env.ref(action_xmlid).id,
        )
        # send mail template to users having email address
        template = self.env.ref(template_xmlid)
        template_ctx = {'action_url': action_url}
        if additionnal_values:
            template_ctx.update(additionnal_values)
        for employee in employees:
            template.with_context(**template_ctx).send_mail(employee.id)
            _logger.info("A reminder sent to user '%s'.", employee.name)
