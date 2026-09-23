# Copyright 2026 Nuxly
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Account closing multi company",
    "summary": "Review and update accounting lock dates across several companies at once",
    "version": "19.0.1.0.",
    "category": "Accounting",
    "website": "https://github.com/nuxly/nuxly-odoo-addons",
    "author": "Nuxly",
    "license": "AGPL-3",
    "depends": ["base", "account"],
    "data": [
        "security/ir.model.access.csv",
        "views/account_closing_multi_wizard_views.xml",
        "views/res_company_views.xml",
    ],
    "installable": True,
    "application": False,
}
