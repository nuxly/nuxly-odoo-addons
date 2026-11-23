# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Company switcher preferred users",
    "summary": "Preferred users on companies, who see them first in their company switcher",
    "version": "19.0.1.0.0",
    "category": "Extra Tools",
    "website": "https://github.com/nuxly/nuxly-odoo-addons",
    "author": "Nuxly",
    "license": "LGPL-3",
    "depends": ["web"],
    "data": [
        "views/res_company_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "web_company_switcher_preferred_user/static/src/xml/switch_company_item.xml",
        ],
    },
    "installable": True,
    "application": False,
}
