# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'l10n_fr_fec_unique',
    'version': '16.0.0.0',
    'category': 'Accounting & Finance',
    'summary': 'Export comptable unique',
    'description': """
    This module generates FEC file with unique export
======================================================================

For any question, send us an email to info@nuxly.com

Features:
-----------------------------------------------------------
    """,
    'author': 'Nuxly',
    'website': 'https://www.nuxly.com',
    'depends': ['l10n_fr_fec'],
    'data': [
        'views/account_fr_fec_view.xml',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'licence' : 'LGPL-3',
}
