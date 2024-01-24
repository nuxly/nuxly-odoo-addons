from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import logging
from odoo import models, _

logger = logging.getLogger(__name__)


class TimesheetSummary(models.TransientModel):
    _name = 'timesheet.summary'
    _description = "Daily summary of time spent for each manager"

    # Send a summary of timesheet lines entered by employees
    def _cron_timesheet_summary_manager(self):
        managers = self.get_managers()
        action_url = '%s/web#menu_id=%s&action=%s' % (
            self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
            self.env.ref('hr_timesheet.timesheet_menu_root').id,
            self.env.ref('hr_timesheet.act_hr_timesheet_line').id,
        )
        template = self.env.ref('reminder_summary_timesheet.mail_template_timesheet_summary_manager')
        template_ctx = {'action_url': action_url}
        for manager in managers:
            template.with_context(template_ctx).send_mail(manager.id)
            logger.info("Summaries of time spent to send to the manager '%s'.", manager.name)


    # Return managers responsible for approving timesheet lines
    def get_managers(self):
        managers = []

        # Retrieves managers distinct from all employees
        for employee in self.env['hr.employee'].search([('timesheet_manager_id', '!=', False)]):
            if employee['timesheet_manager_id'] not in managers:
                managers += employee['timesheet_manager_id']
        return managers


    # Return the different summary tables of timesheet lines for a given manager
    def get_summarized_analytic_lines(self, manager):
        date_today = date.today()

        # Retrieves the summary of today timesheet lines
        today = date_today.strftime("%Y-%m-%d")
        daily_times = self.get_analytic_lines(today, today, manager)
        daily_times_summarized = self.summarize_analytic_lines(daily_times), _('Today summary')
        
        # Retrieves the summary of the previous working day timesheet lines
        date_yesterday = date_today + relativedelta(days=-3) if date_today.weekday() == 0 else date_today + relativedelta(days=-1)
        yesterday = date_yesterday.strftime("%Y-%m-%d")
        yesterday_times = self.get_analytic_lines(yesterday, yesterday, manager)
        yesterday_times_summarized = self.summarize_analytic_lines(yesterday_times), _('Previous working day summary')
        
        # Retrieves the summary of the current week timesheet lines
        date_monday = (date_today - timedelta(days=date_today.weekday()+2)).strftime("%Y-%m-%d")
        weekly_times = self.get_analytic_lines(date_monday, date_today, manager)
        weekly_times_summarized = self.summarize_analytic_lines(weekly_times), _('Total of the week')
        
        # Retrieves the summary of the current month timesheet lines
        date_start_month = date(date_today.year, date_today.month, 1).strftime("%Y-%m-%d")
        monthly_times = self.get_analytic_lines(date_start_month, date_today, manager)
        monthly_times_summarized = self.summarize_analytic_lines(monthly_times), _('Total of the month')

        res = daily_times_summarized, yesterday_times_summarized, weekly_times_summarized, monthly_times_summarized
        return res


    # Returns the timesheet lines of a given manager's employees based on a given range
    def get_analytic_lines(self, date_start, date_end, manager):
        employees = self.env['hr.employee'].search([
            ("timesheet_manager_id", "=", manager.id
            )])
        employee_ids = [employee['id'] for employee in employees]

        aal = self.env['account.analytic.line'].search([
            ("employee_id", "in", employee_ids),
            ("date",">=",date_start),
            ("date","<=",date_end)])
        
        return aal


    # Returns a summary of given timesheet lines
    def summarize_analytic_lines(self, aal):
        if aal:
            # tpi : Total Per Intervener
            # tpp : Total Per Project
            tpi = tpp = "Total"
            intervenants = []
            projets = {}
            # Total time of all projects combined for each interveners
            tpi_dict = {tpi: {tpp: 0}}

            for line in aal:
                projet = line.project_id.name
                intervenant = line.employee_id.user_partner_id.firstname
                temps = line.unit_amount

                # Adding the intervener to the "interveners" table if it is not already entered
                if intervenant not in intervenants:
                    intervenants.append(intervenant)
                # Adding the project to the "projects" table if it is not already entered
                if projet not in projets:
                    projets[projet] = {}
                    projets[projet][tpp] = 0
                # If the intervener is already on the project in the "projects" table then we add the time spent to the time already entered
                if intervenant in projets[projet]:
                    projets[projet][intervenant] += temps
                    tpi_dict[tpi][intervenant] += temps
                    projets[projet][tpp] += temps
                    tpi_dict[tpi][tpp] += temps
                # Otherwise the intervener is added to the project in the “projects” table and their time spent is entered
                else:
                    projets[projet][intervenant] = temps
                    if intervenant not in tpi_dict[tpi]:
                        tpi_dict[tpi][intervenant] = temps
                    else:
                        tpi_dict[tpi][intervenant] += temps
                    projets[projet][tpp] += temps
                    tpi_dict[tpi][tpp] += temps
                
            # Adding a “Total” intervener
            intervenants.append(tpp)
            # Adding a total time line of participants for all projects combined to the “projects” table
            projets.update(tpi_dict)
            res = intervenants, projets
            return res
