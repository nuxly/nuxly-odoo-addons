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
