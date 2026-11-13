# Account report ledger navigation

[![License: AGPL-3](https://img.shields.io/badge/license-AGPL--3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0.html)

Technical name: `account_report_ledger_navigation`

## Description

This module adds **Previous account** and **Next account** buttons to the
general ledger, and **Previous partner** and **Next partner** buttons to
the partner ledger, so that accounts (or partners) can be reviewed one
after the other without going back to the trial balance each time.

The navigation goes through the same accounts (or partners) as the
ledger itself, with the current filters (period, companies, journals,
draft entries...):

- General ledger: accounts with entries up to the end of the period,
  sorted by code. The current account is the one in the search bar,
  which is where Odoo puts the account code when the ledger is opened
  from the trial balance.
- Partner ledger: partners with a balance or entries in the period, in
  the ledger's order. The current partner is the one selected in the
  "Partners" filter, or else the first one matching the search bar.

The next ledger replaces the current one, so the breadcrumb does not
grow at every click.

**This module requires Odoo Enterprise** (it depends on
`account_reports`, licensed under OEEL-1), since that is where the
ledgers it extends live.

## Usage

From the trial balance, open the general ledger of an account (the
**General ledger** option of the account line), then click **Next
account** or **Previous account** to review the following or preceding
account. Without any account in the search bar, **Next account** opens
the first account and **Previous account** the last one.

In the partner ledger, select a partner in the **Partners** filter (or
type its name in the search bar), then click **Next partner** or
**Previous partner**. Each partner is then opened alone, unfolded.

A message is shown when there is no account (or partner) further in
that direction.

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
