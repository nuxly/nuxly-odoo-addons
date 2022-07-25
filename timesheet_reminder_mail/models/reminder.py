from datetime import datetime, date
import logging
from odoo import models

_logger = logging.getLogger(__name__)


class Reminder(models.TransientModel):
    _name = 'timesheet.reminder'
    _description = "Alert each user that doesn't wrote at least one line of time on timesheet"

    def _cron_reminder(self):
        publicHoliday = self.env['hr.holidays.public.line']
        leave = self.env['hr.leave']
        timesheet = self.env['account.analytic.line']
        hrEmployee = self.env['hr.employee']

        today = date.today()
        today_time = datetime.now()

        # Checking working day (not weekend)
        if today.weekday() in [0,1,2,3,4]:
            # checking if day is a holiday
            holiday = publicHoliday.search([]).filtered(lambda x: x.date == today)
            if not holiday:
                # Check for all employees, if each one write at least one line of timesheet
                employees = hrEmployee.search([])
                for employee in employees:
                    if employee.id != 8:
                        continue
                    # Check if each one doesn't on leave
                    onLeave = leave.search([('employee_id', '=', employee.id)]).filtered(lambda
                                                                                             x: x.number_of_days == 1.0 and x.date_from == today_time or x.date_from <= today_time <= x.date_to)
                    if not onLeave:
                        # Check if each one write at least one line of timesheet, or do a alert
                        lines = timesheet.search([('date', '=', today), ('employee_id', '=', employee.id)])
                        if not lines:
                            # TODO a faire un rappel pour saisir les temps
                            template_obj = self.env.ref('timesheet_reminder_mail.reminder_timesheet_fill')
                            if template_obj:
                                receipt_list = [employee.work_email]

                                body = template_obj.body_html

                                mail_values = {
                                    'subject': template_obj.subject,
                                    'body_html': body,
                                    'email_to': ';'.join(map(lambda x: x, receipt_list)),
                                    'email_from': template_obj.email_from,
                                }
                                stat_send = self.env['mail.mail'].create(mail_values).send()
                                _logger.debug("Timesheet Reminder Mail ==> mail sent status to reminder to fill those time on timesheet '%s'.", stat_send)
