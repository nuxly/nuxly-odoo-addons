# Copyright 2026 Nuxly
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "HR Expense Mileage",
    "summary": "Manage mileage claims in employee expenses",
    "version": "19.0.1.4.0",
    "category": "Human Resources/Expenses",
    "website": "https://github.com/nuxly/nuxly-odoo-addons",
    "author": "Nuxly",
    "license": "AGPL-3",
    "depends": ["hr_expense", "fleet"],
    "data": [
        "security/ir.model.access.csv",
        "data/product_template_data.xml",
        "data/hr_expense_ma_fuel_type_data.xml",
        "views/product_product_views.xml",
        "views/fleet_vehicle_views.xml",
        "views/hr_employee_views.xml",
        "views/hr_expense_ma_scale_views.xml",
    ],
    "installable": True,
    "application": False,
}
