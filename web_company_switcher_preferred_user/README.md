# Company switcher preferred users

[![License: LGPL-3](https://img.shields.io/badge/license-LGPL--3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0.html)
![Odoo 19.0](https://img.shields.io/badge/odoo-19.0-714B67.svg)

Technical name: `web_company_switcher_preferred_user`

## Description

In multi-company setups, the company switcher (top-right of the navbar)
quickly becomes a long list, and users keep looking for the companies
they work on.

This module adds **Preferred users** on companies. In the company
switcher, each user sees first the companies they are a preferred user
of, then the other companies in the usual order. A company can have
several preferred users.

Only the order of the switcher changes, for each user: nothing is
written in the database, the access rights are not changed and the other
users keep their own order.

The label and help of the field can be changed by another module to fit
a business need (e.g. "Accountants").

## Usage

In **Settings > Companies**, open a company and add its **Preferred
users** (right below the parent company).

When one of these users opens the company switcher (after a page
reload), the companies they are a preferred user of are listed first, in
their usual order among themselves and marked with a star, followed by
the other companies.

## Technical notes

- Field `preferred_user_ids` (many2many, internal users only) on
  `res.company`.
- The order is changed in `ir.http.session_info`: the sequence sent to the
  browser of the companies the user is a preferred user of is lowered,
  for this user only. The native switcher sorts by sequence, so no
  JavaScript is needed.
- These companies are also flagged `is_preferred` in the session, and
  an extension of the `web.SwitchCompanyItem` template shows a star on
  their right in the switcher.
- Compatible with `web_multi_company_counter`.

## Credits

### Contributors

- Nuxly <https://github.com/nuxly>
