This module extends Odoo's own "Lock Journal Entries" wizard
(`account.change.lock.date`, from Odoo Accounting) to target several
companies at once instead of only the current one.

Most of the native wizard is kept as-is: the draft-entries warning and
the lock exception automatism (moving a lock date backward never
rewrites a company's official lock date — a temporary exception is
granted instead, for the current user or for everyone, for a limited
time or indefinitely). A handful of methods were adapted so they apply
to every selected company instead of a single one.

Two differences from the native wizard: the irreversible hard lock is
out of scope for this module (removed from the form entirely), and a
"Next monthly period" button lets any user preview the four lock dates
advanced to their own next month-end before applying them.

**This module requires Odoo Enterprise** (it depends on
`account_accountant`, licensed under OEEL-1), since that is where the
lock date wizard it extends lives.
