# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Multi-Company Selection Counter",
    "summary": "Systray badge showing how many companies are currently selected",
    "version": "19.0.1.1.0",
    "category": "Extra Tools",
    "author": "Nuxly",
    "license": "LGPL-3",
    "depends": ["web"],
    "assets": {
        "web.assets_backend": [
            "web_multi_company_counter/static/src/xml/multi_company_counter.xml",
            "web_multi_company_counter/static/src/scss/multi_company_counter.scss",
        ],
    },
    "installable": True,
    "application": False,
}
