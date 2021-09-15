{
    'name': 'ASCII Export for ISACOMPTA',
    'version': '14.0.0.0',
    'category': 'Accounting & Finance',
    'summary': 'Export comptable for ISACOMPTA',
    'description': """
This module generates an ASCII export file for ISACOMPTA.
======================================================================

For any question, send us an email to info@nuxly.com

Features:
-----------------------------------------------------------
    """,
    'author': 'Nuxly',
    'website': 'https://www.nuxly.com',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/export_isacompta.xml',
        'views/res_company.xml',
        'views/res_partner.xml',
    ],
    'installable': True,
}
