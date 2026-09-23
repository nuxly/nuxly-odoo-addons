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

Two differences from the native wizard: the irreversible hard lock is
out of scope for this module (removed from the form entirely), and a
"Next monthly period" button lets any user preview the four lock dates
advanced to their own next month-end before applying them.

**This module requires Odoo Enterprise** (it depends on
`account_accountant`, licensed under OEEL-1), since that is where the
lock date wizard it extends lives.

## Usage

Open Accounting ▸ Accounting ▸ Closing ▸ Period closing to see the lock
dates of every company, then select one or more companies and click
**Close** (or use the row button) to open the wizard — it is Odoo's own
"Lock Journal Entries" form, with the selected companies shown at the
top instead of a single one.

Click **Next monthly period** to fill the four lock date fields with
their next month-end (nothing is applied yet), or edit them manually,
then click **Apply**. If a date would move a company's lock backward,
choose who the exception applies to and for how long instead of picking
a date that moves forward.

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
