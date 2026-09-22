# Account Multi-Company Closing

[![License: AGPL-3](https://img.shields.io/badge/license-AGPL--3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0.html)

Technical name: `account_closing_multi_company`

## Description

This module adds a "Period Closing" screen to review, at a glance, the
accounting lock dates (Sales, Purchase, Tax, Lock Everything) of every
company the current user has access to, and update several companies at
once from a single wizard instead of opening each company's settings form
individually.

Two distinct actions are available, depending on the user's role:

- Any accounting user can close the next monthly period: each selected
  company is advanced, independently, to the end of the month following
  its own current lock date. The tax lock date is never touched by this
  action.
- An accounting manager can additionally force arbitrary lock dates,
  identically, on all selected companies at once.

A lock date can never be set in the future.

## Usage

Open Accounting ▸ Accounting ▸ Closing ▸ Period Closing to see the lock
dates of every company, then:

1. Select one or more companies in the list and click **Close** (or use
   the row button) to open the wizard.
2. Click **Close Next Monthly Period** to advance the selected companies
   to the end of the following month, or, as an accounting manager, edit
   the four lock date fields and click **Close** to force those exact
   dates on all selected companies.

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
