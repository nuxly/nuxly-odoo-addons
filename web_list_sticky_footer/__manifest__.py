# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Account List Sticky Footer",
    "summary": "Sticky footer for account list views only",
    "version": "19.0.1.0.0",
    "category": "Accounting",
    "author": "Nuxly",
    "license": "LGPL-3",
    "depends": ["web", "account"],
    "assets": {
        "web.assets_backend": [
            "web_list_sticky_footer/static/src/js/sticky_footer.esm.js",
            "web_list_sticky_footer/static/src/scss/list_sticky_footer.scss",
        ],
    },
    "installable": True,
    "application": False,
}
