{
    'name': 'Nuxly',
    'version': '14.0.0.0',
    'category': 'Specific',
    'summary': 'Module pour Nuxly',
    'description': """
DESCRIPTION
-----------
Module spécifique pour Nuxly.
""",
    'author': 'Nuxly',
    'website': 'https://www.nuxly.com',
    'depends' : ['base', 'analytic', 'hr', 'hr_timesheet', 'account', 'crm'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_analytic_timesheet.xml',
        'views/global_timesheet_state.xml',
        'views/crm_lead_suivi_gdoc.xml'
    ],
    'installable': True,
    'auto_install': True,
}