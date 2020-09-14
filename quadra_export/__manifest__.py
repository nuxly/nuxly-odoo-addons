{
    'name': 'Export QUADRA Format (CSV)',
    'version': '13.0.3.0',
    'category': 'Accounting & Finance',
    'description': """
This module make an export to CSV format for QUADRA.
======================================================================

For any ask, send a mail to info@nuxly.com

Features:
-----------------------------------------------------------
    * Analytics (1 axe)
    """,
    'author': 'Nuxly',
    'website': 'http://www.nuxly.com',
    'depends': ['account'],
    'data': [
        'wizard/export_quadra.xml',
        'views/res_company.xml',
        'views/res_partner.xml',
    ],
    'installable': True,
}
