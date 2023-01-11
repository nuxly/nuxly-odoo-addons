# -*- coding: utf-8 -*-
{
    'name': "Background customization",

    'summary': """
        Background customization for web client and login screen""",

    'description': """
        Customize odoo background (overlayed image, colors) for web client and login screen.
    """,

    'author': "Nuxly",
    'website': "https://www.nuxly.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Technical',
    'version': '14.0.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web_enterprise'],

    # always loaded
    'data': [
        'views/templates.xml',
    ],
}
