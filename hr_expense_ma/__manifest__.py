# Copyright 2026 Nuxly
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "HR Expense Mileage",
    "summary": "Manage mileage claims in employee expenses",
    "version": "19.0.1.1.0",
    "category": "Human Resources/Expenses",
    "website": "https://github.com/nuxly/nuxly-odoo-addons",
    "author": "Nuxly",
    "license": "AGPL-3",
    "depends": ["hr_expense", "fleet"],
    "data": [
        "data/product_template_data.xml",
        "views/product_template_views.xml",
    ],
    "installable": True,
    "application": False,
}
