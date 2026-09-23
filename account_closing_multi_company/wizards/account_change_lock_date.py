import calendar
from datetime import date, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.fields import Domain

from odoo.addons.account.models.company import SOFT_LOCK_DATE_FIELDS

EXCEPTION_DURATIONS = {
    "5min": timedelta(minutes=5),
    "15min": timedelta(minutes=15),
    "1h": timedelta(hours=1),
    "24h": timedelta(hours=24),
    "forever": False,
}


class AccountChangeLockDate(models.TransientModel):
    """Extends Odoo's own lock date wizard to target several companies at once, instead of only the
    current one. The exception/warning automatisms and the form itself stay Odoo's own; only the
    handful of methods that assumed a single company are adapted here. The irreversible hard lock is
    out of scope for this module (removed from the view, never touched by these overrides)."""

    _inherit = "account.change.lock.date"

    company_id = fields.Many2one(default=lambda self: self._get_target_companies()[:1])
    company_ids = fields.Many2many(
        "res.company", string="Companies", default=lambda self: self._get_target_companies()
    )
    sale_lock_date = fields.Date(default=lambda self: self._get_target_companies()[:1].sale_lock_date)
    purchase_lock_date = fields.Date(default=lambda self: self._get_target_companies()[:1].purchase_lock_date)
    tax_lock_date = fields.Date(default=lambda self: self._get_target_companies()[:1].tax_lock_date)
    fiscalyear_lock_date = fields.Date(default=lambda self: self._get_target_companies()[:1].fiscalyear_lock_date)

    def _get_target_companies(self):
        """Companies targeted by the closing: the action's active_ids, or the current company."""
        active_ids = self.env.context.get("active_ids") or (
            [self.env.context["active_id"]] if self.env.context.get("active_id") else []
        )
        return self.env["res.company"].browse(active_ids).exists() if active_ids else self.env.company

    def _get_companies(self):
        self.ensure_one()
        return self.company_ids or self.env.company

    def _check_not_future(self, lock_date):
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
        values = {field: self._next_month_end(self[field]) for field in SOFT_LOCK_DATE_FIELDS}
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

    def _get_draft_moves_in_locked_period_domain(self):
        """Same as Odoo's own method, combined across every selected company instead of only the
        current one (delegates to the original per-company logic via with_company, no logic copied).
        sudo() is required here: an accounting manager can review/lock any company through this
        wizard even if that company isn't in their own personal allowed companies."""
        self.ensure_one()
        domain = Domain.FALSE
        for company in self._get_companies():
            domain |= super(AccountChangeLockDate, self.sudo().with_company(company))._get_draft_moves_in_locked_period_domain()
        return domain

    @api.depends("company_ids")
    @api.depends_context("user", "company")
    def _compute_lock_date_exceptions(self):
        """Same idea as Odoo's own compute, but looking for active exceptions across every selected
        company. When several companies are selected, this reflects the earliest exception found for
        each field across all of them (a per-company breakdown isn't shown, to keep this simple)."""
        for wizard in self:
            companies = wizard._get_companies()
            Exception_ = self.env["account.lock_exception"]
            exceptions = Exception_
            for company in companies:
                # _get_active_exceptions_domain() is meant to be passed straight to search(), not
                # combined with other domains (it returns a 1-item tuple, not a bare Domain) - search
                # per company and union the resulting records instead, like Odoo's own callers do.
                exceptions |= Exception_.search(Exception_._get_active_exceptions_domain(company, SOFT_LOCK_DATE_FIELDS))
            for field in SOFT_LOCK_DATE_FIELDS:
                field_exceptions = exceptions.filtered(lambda e, field=field: e.lock_date_field == field)
                field_exceptions_for_me = field_exceptions.filtered(lambda e: e.user_id.id == self.env.user.id)
                field_exceptions_for_everyone = field_exceptions.filtered(lambda e: not e.user_id.id)
                min_for_me = min(field_exceptions_for_me, key=lambda e, field=field: e[field] or date.min) if field_exceptions_for_me else False
                min_for_everyone = min(field_exceptions_for_everyone, key=lambda e, field=field: e[field] or date.min) if field_exceptions_for_everyone else False
                wizard[f"min_{field}_exception_for_me_id"] = min_for_me
                wizard[f"min_{field}_exception_for_everyone_id"] = min_for_everyone
                wizard[f"{field}_for_me"] = min_for_me.lock_date if min_for_me else False
                wizard[f"{field}_for_everyone"] = min_for_everyone.lock_date if min_for_everyone else False

    def _get_changes_needing_exception(self):
        """A field needs an exception if it would move at least one selected company's lock date
        backward instead of advancing it."""
        self.ensure_one()
        changes = {}
        for field in SOFT_LOCK_DATE_FIELDS:
            for company in self._get_companies():
                if company[field] and (not self[field] or self[field] < company[field]):
                    changes[field] = self[field]
                    break
        return changes

    def _prepare_exception_values(self):
        """One exception per (company, field) that needs it, instead of a single company."""
        self.ensure_one()
        if self.exception_applies_to == "everyone" and self.exception_duration == "forever":
            return False
        if not self._get_changes_needing_exception():
            return False

        errors = []
        if not self.exception_applies_to:
            errors.append(_("You need to select who the exception applies to."))
        if not self.exception_duration:
            errors.append(_("You need to select a duration for the exception."))
        if errors:
            raise UserError("\n".join(errors))

        base_vals = {"user_id": False if self.exception_applies_to == "everyone" else self.env.user.id}
        duration = EXCEPTION_DURATIONS[self.exception_duration]
        if duration:
            base_vals["end_datetime"] = self.env.cr.now() + duration
        if self.exception_reason:
            base_vals["reason"] = self.exception_reason

        exception_vals_list = []
        for company in self._get_companies():
            for field in SOFT_LOCK_DATE_FIELDS:
                if company[field] and (not self[field] or self[field] < company[field]):
                    exception_vals_list.append({**base_vals, "company_id": company.id, field: self[field]})
        return exception_vals_list or False

    def _prepare_lock_date_values(self, company, exception_vals_list=None):
        """Same guards as Odoo's own method, for one of the selected companies (soft lock dates only;
        the hard lock date is out of scope for this module)."""
        self.ensure_one()
        lock_date_values = {field: self[field] for field in SOFT_LOCK_DATE_FIELDS if self[field] != company[field]}
        for lock_date in lock_date_values.values():
            self._check_not_future(lock_date)

        if exception_vals_list:
            for exception_vals in exception_vals_list:
                if exception_vals.get("company_id") == company.id:
                    for field in SOFT_LOCK_DATE_FIELDS:
                        if field in exception_vals:
                            lock_date_values.pop(field, None)
        return lock_date_values

    def _change_lock_date(self, company, lock_date_values=None):
        """Same as Odoo's own method (report hooks included), for one of the selected companies."""
        self.ensure_one()
        if lock_date_values is None:
            lock_date_values = self._prepare_lock_date_values(company)

        tax_lock_date = lock_date_values.get("tax_lock_date")
        if tax_lock_date and tax_lock_date != company["tax_lock_date"]:
            self.sudo().with_company(company)._create_default_report_external_values("tax_lock_date")

        fiscalyear_lock_date = lock_date_values.get("fiscalyear_lock_date")
        if fiscalyear_lock_date and fiscalyear_lock_date != company.fiscalyear_lock_date:
            self.sudo().with_company(company)._create_default_report_external_values("fiscalyear_lock_date")

        company.sudo().write(lock_date_values)

    def change_lock_date(self):
        """Same permission check and flow as Odoo's own method, applied to every selected company:
        exceptions are created once for all companies that need one, then each company gets its own
        direct lock date write for the fields that don't need an exception."""
        self.ensure_one()
        if not self.env.user.has_group("account.group_account_manager"):
            raise UserError(_("Only an accounting administrator is allowed to change lock dates."))

        exception_vals_list = self._prepare_exception_values()
        if exception_vals_list:
            # account.lock_exception.create() pops the lock-date field key out of each vals dict it
            # receives; pass copies so exception_vals_list still has it for _prepare_lock_date_values.
            self.env["account.lock_exception"].create([dict(vals) for vals in exception_vals_list])

        for company in self._get_companies():
            lock_date_values = self._prepare_lock_date_values(company, exception_vals_list=exception_vals_list)
            self._change_lock_date(company, lock_date_values)

        return {"type": "ir.actions.act_window_close"}
