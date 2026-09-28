# Account closing multi company

[![License: AGPL-3](https://img.shields.io/badge/license-AGPL--3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0.html)

Technical name: `account_closing_multi_company`

## Description

This module extends Odoo's own "Lock journal entries" wizard
(`account.change.lock.date`, from Odoo Accounting) to target several
companies at once instead of only the current one.

Most of the native wizard is kept as-is: the draft-entries warning and
the lock exception automatism (moving a lock date backward never
rewrites a company's official lock date — a temporary exception is
granted instead, for the current user or for everyone, for a limited
time or indefinitely). A handful of methods were adapted so they apply
to every selected company instead of a single one.

Differences from the native wizard:

- The irreversible hard lock is out of scope for this module (removed
  from the form entirely).
- Each of the four dates has its own "Increment period" button next to
  it, advancing only that date to its own next month-end for preview
  (nothing is applied until "Apply" is pressed). Incrementing "Lock
  everything" also raises any of the other three dates that would
  otherwise end up earlier than it.
- With several companies selected, a date can only be edited here if
  every selected company already shares the exact same value for it —
  a date that differs between companies is hidden, with a message,
  rather than silently forced to one company's value. If none of the
  four dates are common at all, the whole form is replaced by a message
  suggesting to close the companies one at a time instead.

**This module requires Odoo Enterprise** (it depends on
`account_accountant`, licensed under OEEL-1), since that is where the
lock date wizard it extends lives.

## Usage

Open Accounting ▸ Accounting ▸ Closing ▸ Period closing to see the lock
dates of every company, then select one or more companies and click
**Close** (or use the row button) to open the wizard — it is Odoo's own
"Lock Journal Entries" form, with the selected companies shown at the
top instead of a single one.

Click **Increment period** next to a date to preview it advanced to its
next month-end (nothing is applied yet), or edit it manually, then click
**Apply**. If a date would move a company's lock backward, choose who
the exception applies to and for how long instead of picking a date
that moves forward.

With several companies selected, only the dates they already share are
editable; a date that differs between them is hidden with an
explanatory message instead.

## Roadmap

- Additional period-closing features are planned; this module is under
  active development.

## Bug Tracker

Issues are tracked on
[GitHub Issues](https://github.com/nuxly/nuxly-odoo-addons/issues).

## Credits

### Authors

- Nuxly

### Contributors

- Nuxly <https://github.com/nuxly>

### Maintainers

This module is maintained by Nuxly.

## License

This module is licensed under the
[GNU Affero General Public License, version 3](https://www.gnu.org/licenses/agpl-3.0.html).
