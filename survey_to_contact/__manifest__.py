#-*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'survey_to_contact',
    'version': '16.0.0.0',
    "category": "Marketing/Survey",
    'summary': 'Generate contacts from survey',
    'description': """
    This module create or merge contacts from survey.
======================================================================

Special description:
-----------------------------------------------------------
This module was primarily inspired by a Odoo community module from the OCA (Odoo Community Association) repository OCA/survey on GitHub, specifically the 'survey_contact_generation' module from the 15.0 branch.
Github: https://github.com/OCA/survey/tree/15.0

Additions:
-----------------------------------------------------------
A manual way to create contacts via a button has been added (optional display on surveys). This button allows creating or merging a contact from survey responses.

Several modifications have been made, and specific code has been added (generally, specific code starts with z_ or z. ....)

For any question, send us an email to info@nuxly.com

Features:
-----------------------------------------------------------
    """,
    'author': 'Nuxly',
    'website': 'https://www.nuxly.com',
    'depends': ['base',
                'survey',
                'contacts'
                ],
    'data': [
        # SECURITY
        'security/ir.model.access.csv',
        # VIEWS
        'views/survey_user_views.xml',
        'views/survey_question_views.xml',
        'views/survey_survey_views.xml',
        'wizard/z_create_partner_views.xml',
        'data/mail_templates_chatter.xml',
    ],
    'installable': True,
    "license": "AGPL-3",
}
