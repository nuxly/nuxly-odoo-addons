from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import logging
from odoo import models

logger = logging.getLogger(__name__)


class Summary(models.TransientModel):
    _name = 'timesheet.summary'

    def _cron_timesheet_summary_manager(self):
        managers = self.get_managers()
        action_url = '%s/web#menu_id=%s&action=%s' % (
            self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
            self.env.ref('hr_timesheet.timesheet_menu_root').id,
            self.env.ref('hr_timesheet.act_hr_timesheet_line').id,
        )
        # send mail template to users having email address
        template = self.env.ref('timesheet_reminder_mail.mail_template_timesheet_summary_manager')
        template_ctx = {'action_url': action_url}
        for manager in managers:
            template.with_context(template_ctx).send_mail(manager.id)
            logger.debug("=============================> RESULTAT : %s", template_ctx)
            logger.info("Summaries of time spent to send to the manager '%s'.", manager.name)


    # Retoune les managers responsablent d'approuver les feuilles de temps
    def get_managers(self):
        hr_employee = self.env['hr.employee']
        managers = []

        # Récupération des employés aillant un manager
        employees = hr_employee.search([('timesheet_manager_id', "!=", False)])

        # Parcours ces employés en sortant les managers
        for employee in employees:
            if employee['timesheet_manager_id'] not in managers:
                managers += employee['timesheet_manager_id']
        return managers


    # Retoune les différents tableaux de temps d'un manager
    def get_summarized_analytic_lines(self, manager):
        date_today = date.today()

        # Récupération des temps du jour
        today = date_today.strftime("%Y-%m-%d")
        daily_times = self.get_analytic_lines(today, today, manager)
        daily_times_summarized = self.summarize_analytic_lines(daily_times), "Temps du jour"
        
        # Récupération des temps de la veille ouvrée
        date_yesterday = date_today + relativedelta(days=-3) if date_today.weekday() == 0 else date_today + relativedelta(days=-1)
        yesterday = date_yesterday.strftime("%Y-%m-%d")
        yesterday_times = self.get_analytic_lines(yesterday, yesterday, manager)
        yesterday_times_summarized = self.summarize_analytic_lines(yesterday_times), "Temps de la veille"
        
        # Récupération des temps de la semaine
        date_monday = (date_today - timedelta(days=date_today.weekday()+2)).strftime("%Y-%m-%d")
        weekly_times = self.get_analytic_lines(date_monday, date_today, manager)
        weekly_times_summarized = self.summarize_analytic_lines(weekly_times), "Cumule de la semaine"
        
        # Récupération des temps du mois
        date_start_month = date(date_today.year, date_today.month, 1).strftime("%Y-%m-%d")
        monthly_times = self.get_analytic_lines(date_start_month, date_today, manager)
        monthly_times_summarized = self.summarize_analytic_lines(monthly_times), "Cumule du mois"

        res = daily_times_summarized, yesterday_times_summarized, weekly_times_summarized, monthly_times_summarized
        return res


    # Retourne les temps passés des employées en fonction d'un manager et d'un plage données
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


    # Retourne une synthèse des temps passés
    def summarize_analytic_lines(self, aal):
        if aal:
            # tpi : total par intervenant
            # tpp : total par projet
            tpi = tpp = "Total"
            intervenants = []
            projets = {}
            # temps total des intervenants pour tous projets confondus
            tpi_dict = {tpi: {tpp: 0}}

            for line in aal:
                projet = line.project_id.name
                intervenant = line.employee_id.user_partner_id.firstname
                temps = line.unit_amount

                # Ajout de l'intervenant dans le tableau "intervenants" s'il n'existe pas déjà
                if intervenant not in intervenants:
                    intervenants.append(intervenant)
                # Ajout de le projet dans le tableau "projets" s'il n'existe pas déjà
                if projet not in projets:
                    projets[projet] = {}
                    projets[projet][tpp] = 0
                # Si l’intervenant est déjà sur le projet du tableau "projets" alors on additionne le temps passé au temps déjà renseigné
                if intervenant in projets[projet]:
                    projets[projet][intervenant] += temps
                    tpi_dict[tpi][intervenant] += temps
                    projets[projet][tpp] += temps
                    tpi_dict[tpi][tpp] += temps
                # Sinon l’intervenant est ajouté sur le projet du tableau "projets" et son temps passé est renseigné
                else:
                    projets[projet][intervenant] = temps
                    if intervenant not in tpi_dict[tpi]:
                        tpi_dict[tpi][intervenant] = temps
                    else:
                        tpi_dict[tpi][intervenant] += temps
                    projets[projet][tpp] += temps
                    tpi_dict[tpi][tpp] += temps
                
            # Ajout d'un intervenant "Total"
            intervenants.append(tpp)
            # Ajout d'une ligne de temps total des intervenants pour tous projets confondus au tableau des projets
            projets.update(tpi_dict)
            res = intervenants, projets
            return res
