{
    'name': 'ASCII Export for QUADRATUS (fixed width)',
    'version': '13.0.3.0',
    'category': 'Accounting & Finance',
    'description': """
This module generates an ASCII export file (fixed width) for QUADRATUS.
======================================================================

For any question, send us an email to info@nuxly.com

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
