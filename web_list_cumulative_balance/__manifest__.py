# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Account List Cumulative Balance",
    "summary": "Live cumulative balance column on account move line list views",
    "version": "19.0.1.1.0",
    "category": "Accounting",
    "author": "Nuxly",
    "license": "LGPL-3",
    "depends": ["web", "account"],
    "data": [
        "views/account_move_line_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "web_list_cumulative_balance/static/src/js/cumulative_balance_field.esm.js",
            "web_list_cumulative_balance/static/src/xml/cumulative_balance_field.xml",
        ],
    },
    "installable": True,
    "application": False,
}
