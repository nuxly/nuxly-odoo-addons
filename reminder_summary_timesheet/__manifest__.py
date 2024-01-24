{
    'name': 'Reminders and summaries for timesheet lines',
    'version': '16.0.0.0',
    'category': 'HR',
    'summary': 'Remind employees to fill their timesheets and summarize them to managers',
    'description': """
DESCRIPTION
-----------
This module sends an email notification to each user who hasn't provided at least one timesheet line and that is not in vacation.
In addition, it sends a daily summary to the manager. In addition, it sends a daily summary to managers. It is presented in the form of tables:
    - timesheet lines of today
    - timesheet lines of the past working day
    - timesheet lines of current week
    - timesheet lines of current month
""",
    'author': 'Nuxly',
    'website': 'https://www.nuxly.com',
    'depends' : [
        'base',
        'hr_timesheet',
        'hr_holidays_public'
    ],
    'data': [
        'data/reminder_cron.xml',
        'views/mail.xml',
        'views/hr_view.xml',
    ],
    'installable': True,
    'auto_install': True,
    'application': True,
    "license": "AGPL-3",
}
