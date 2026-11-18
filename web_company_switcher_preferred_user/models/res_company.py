from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    preferred_user_ids = fields.Many2many(
        "res.users",
        "res_company_preferred_user_rel",
        "company_id",
        "user_id",
        string="Preferred users",
        domain=[("share", "=", False)],
        help="Internal users working on this company. The company is listed first in their company switcher.",
    )
