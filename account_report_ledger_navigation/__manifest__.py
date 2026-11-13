# Copyright 2026 Nuxly
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Account report ledger navigation",
    "summary": "Previous / next account and partner buttons on the general and partner ledgers",
    "version": "19.0.1.0.0",
    "category": "Accounting",
    "website": "https://github.com/nuxly/nuxly-odoo-addons",
    "author": "Nuxly",
    "license": "AGPL-3",
    "depends": ["web", "account", "account_reports"],
    "assets": {
        "web.assets_backend": [
            "account_report_ledger_navigation/static/src/js/account_report_controller.esm.js",
        ],
    },
    "installable": True,
    "application": False,
}
