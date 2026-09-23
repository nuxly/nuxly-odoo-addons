# Account closing multi company

[![License: AGPL-3](https://img.shields.io/badge/license-AGPL--3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0.html)

Technical name: `account_closing_multi_company`

## Description

This module adds a "Period closing" screen to review, at a glance, the
accounting lock dates (sales, purchase, tax, lock everything) of every
company the current user has access to, and update several companies at
once from a single wizard instead of opening each company's settings form
individually.

Any user can preview the next monthly period: the four lock dates shown
in the wizard are replaced by their own next month-end, for review. This
only updates the wizard, nothing is written to the companies yet.

Only an accounting manager can apply the dates shown in the wizard,
identically, on all selected companies at once — either the previewed
next period, or dates entered manually.

A lock date can never be set in the future.

## Usage

Open Accounting ▸ Accounting ▸ Closing ▸ Period closing to see the lock
dates of every company, then:

1. Select one or more companies in the list and click **Close** (or use
   the row button) to open the wizard.
2. Click **Next monthly period** to fill the four lock date fields with
   their next month-end (nothing is applied yet), or edit them manually.
3. As an accounting manager, click **Apply** to write those dates,
   identically, on all selected companies.

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
