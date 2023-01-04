{
    'name': 'Reminder_timesheet',
    'version': '14.0.0.0',
    'category': 'HR',
    'summary': 'Module to reminder timesheet',
    'description': """
DESCRIPTION
-----------
This module send a notificaton by mail to each user doesn't wrote at least one of time on timesheet.
""",
    'author': 'Nuxly',
    'website': 'https://www.nuxly.com',
    'depends' : ['base', 'hr_timesheet', 'hr_holidays_public'],
    'data': [
        'data/reminder_cron.xml',
        'views/mail.xml',
        'views/hr_view.xml',
    ],
    'installable': True,
    'auto_install': True,
    'application': True,
}
