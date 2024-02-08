#-*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'partner_name_unique',
    'version': '16.0.0.0',
    'category': "Customer Relationship Management",
    'summary': 'Unique contact name',
    'description': """
    This module find partners with duplicate names add a warning.
======================================================================

For any question, send us an email to info@nuxly.com

Features:
-----------------------------------------------------------
    """,
    'author': 'Nuxly',
    'website': 'https://www.nuxly.com',
    'depends': ['base'],
    'data': [
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'licence' : 'LGPL-3',
}
