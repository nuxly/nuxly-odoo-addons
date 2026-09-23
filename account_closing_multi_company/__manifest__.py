# Copyright 2026 Nuxly
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Account closing multi company",
    "summary": "Review and update accounting lock dates across several companies at once",
    "version": "19.0.2.1.1",
    "category": "Accounting",
    "website": "https://github.com/nuxly/nuxly-odoo-addons",
    "author": "Nuxly",
    "license": "AGPL-3",
    "depends": ["base", "account", "account_accountant"],
    "data": [
        "views/account_change_lock_date_views.xml",
        "views/res_company_views.xml",
    ],
    "installable": True,
    "application": False,
}
