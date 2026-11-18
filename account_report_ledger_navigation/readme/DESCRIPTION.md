This module adds **Previous account** and **Next account** buttons to the
general ledger, so that accounts can be reviewed one after the other
without going back to the trial balance each time.

The navigation goes through the accounts listed on screen:

- The accounts of the general ledger with the current filters (period,
  companies, journals, draft entries...), sorted by code.
- When a search is typed in the search bar, only the accounts this search
  shows on screen, exactly as Odoo filters the lines (an account also
  shows up when one of its journal items, or its account group, matches
  the search).
- When the general ledger is opened from the trial balance, only the
  accounts the trial balance shows on screen with its own search.

The current account is the one in the search bar, which is where Odoo
puts the account code when the ledger is opened from the trial balance.
The next ledger replaces the current one, so the breadcrumb does not
grow at every click.

Opened again from the menu, the general ledger shows all accounts and the
navigation starts from scratch, even though Odoo keeps the last options
of the report in the browser session.

**This module requires Odoo Enterprise** (it depends on
`account_reports`, licensed under OEEL-1), since that is where the
general ledger it extends lives.
