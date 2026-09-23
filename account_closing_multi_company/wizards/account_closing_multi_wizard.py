import calendar
from datetime import date, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError

LOCK_DATE_FIELDS = ("sale_lock_date", "purchase_lock_date", "tax_lock_date", "fiscalyear_lock_date")


class AccountClosingMultiWizard(models.TransientModel):
    _name = "account.closing.multi.wizard"
    _description = "Multi-company period closing"

    company_ids = fields.Many2many(
        "res.company", string="Companies", default=lambda self: self._get_target_companies(), readonly=True
    )
    is_multi_company = fields.Boolean(string="Multi-company", compute="_compute_flags")
    is_accounting_admin = fields.Boolean(string="Accounting administrator", compute="_compute_flags")

    sale_lock_date = fields.Date(
        string="Sales lock date", default=lambda self: self._get_target_companies()[:1].sale_lock_date
    )
    purchase_lock_date = fields.Date(
        string="Purchase lock date", default=lambda self: self._get_target_companies()[:1].purchase_lock_date
    )
    tax_lock_date = fields.Date(
        string="Tax return lock date", default=lambda self: self._get_target_companies()[:1].tax_lock_date
    )
    fiscalyear_lock_date = fields.Date(
        string="Lock everything", default=lambda self: self._get_target_companies()[:1].fiscalyear_lock_date
    )

    def _get_target_companies(self):
        """Return the companies targeted by the closing (active window selection, or current company)."""
        active_ids = self.env.context.get("active_ids") or (
            [self.env.context["active_id"]] if self.env.context.get("active_id") else []
        )
        return self.env["res.company"].browse(active_ids).exists() if active_ids else self.env.company

    @api.depends("company_ids")
    def _compute_flags(self):
        """Compute the two booleans driving the view: is_multi_company (several companies selected, to
        adapt the messages) and is_accounting_admin (current user is an accounting manager, to make the
        fields editable and show the "Apply" button)."""
        is_admin = self.env.user.has_group("account.group_account_manager")
        for wizard in self:
            wizard.is_multi_company = len(wizard.company_ids) > 1
            wizard.is_accounting_admin = is_admin

    def _check_not_future(self, lock_date):
        """Guard shared by both actions: refuse any lock date set in the future."""
        if lock_date and lock_date > fields.Date.context_today(self):
            raise UserError(_("You cannot set a lock date in the future."))

    def _next_month_end(self, current_date):
        """End of the month following `current_date`, or end of last month if nothing is locked yet."""
        if not current_date:
            return fields.Date.context_today(self).replace(day=1) - timedelta(days=1)
        month, year = (current_date.month % 12) + 1, current_date.year + (current_date.month // 12)
        return date(year, month, calendar.monthrange(year, month)[1])

    def action_set_next_period_dates(self):
        """Preview only: replace the four lock dates shown in the wizard by their own next month-end.
        Nothing is written to the companies until "Apply" is pressed. Reopens the same wizard instead
        of returning a falsy value, otherwise the dialog framework would close this footer button's
        dialog instead of just refreshing it."""
        self.ensure_one()
        values = {field_name: self._next_month_end(self[field_name]) for field_name in LOCK_DATE_FIELDS}
        for lock_date in values.values():
            self._check_not_future(lock_date)
        self.write(values)
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_apply_forced_dates(self):
        """Accounting administrator: apply the four dates shown in the wizard, identically, on all
        selected companies."""
        if not self.is_accounting_admin:
            raise UserError(_("Only an accounting administrator can apply a lock date on several companies."))
        for field_name in LOCK_DATE_FIELDS:
            self._check_not_future(self[field_name])
        values = {field_name: self[field_name] for field_name in LOCK_DATE_FIELDS}
        self.company_ids.sudo().write(values)
        return {"type": "ir.actions.act_window_close"}
