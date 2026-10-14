# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Multi-Company Selection Counter",
    "summary": "Systray badge showing how many companies are currently selected, "
    "plus shift+click range selection in the company switcher",
    "version": "19.0.1.3.0",
    "category": "Extra Tools",
    "author": "Nuxly",
    "license": "LGPL-3",
    "images": ["static/description/banner.gif"],
    "depends": ["web"],
    "assets": {
        "web.assets_backend": [
            "web_multi_company_counter/static/src/xml/multi_company_counter.xml",
            "web_multi_company_counter/static/src/scss/multi_company_counter.scss",
            "web_multi_company_counter/static/src/js/shift_select.js",
            "web_multi_company_counter/static/src/xml/shift_select.xml",
        ],
    },
    "installable": True,
    "application": False,
}
