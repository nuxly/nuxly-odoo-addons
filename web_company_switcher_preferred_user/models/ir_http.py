from odoo import models

# The company switcher sorts the companies by sequence: lowering it puts them first.
PREFERRED_OFFSET = 1000000


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        """List first, in the company switcher, the companies the user is a preferred user of.

        Only the sequence sent to the browser for this user is lowered: nothing is written in the
        database and the order stays the same for the other users. The companies keep their own
        order among themselves. They are flagged `is_preferred` to show a star in the switcher.
        """
        info = super().session_info()
        allowed = info.get("user_companies", {}).get("allowed_companies")
        if allowed:
            companies = self.env["res.company"].sudo().search(
                [("id", "in", list(allowed)), ("preferred_user_ids", "in", self.env.uid)]
            )
            for company in companies:
                allowed[company.id]["sequence"] -= PREFERRED_OFFSET
                allowed[company.id]["is_preferred"] = True
        return info
