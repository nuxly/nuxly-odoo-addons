# Multi-company selection counter

[![License: LGPL-3](https://img.shields.io/badge/license-LGPL--3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0.html)
![Odoo 19.0](https://img.shields.io/badge/odoo-19.0-714B67.svg)

Technical name: `web_multi_company_counter`

## Description

In multi-company setups, it is easy to lose track of how many companies
are currently selected. Users sometimes think they are working in a
single company while another one is still ticked in the switcher, and
end up confused about which records they are actually looking at.

This module improves Odoo's native company switcher (top-right of the
navbar) in two ways:

- **Selection counter**: a small red badge is displayed directly on the
  company switcher button, showing how many companies are currently
  selected. It only appears once 2 or more companies are selected, so
  single-company users see no difference.
- **Shift+click range selection**: in the company switcher dropdown,
  click a company, then shift+click another one: every company in
  between is selected too, instead of having to tick each one
  individually.

Key points:

- Works on top of the native company switcher: no extra systray icon,
  no new menu.
- The badge updates live as soon as the selection changes.
- Lightweight: only depends on `web`, no Python code, no data, no
  configuration.
- Compatible with Odoo Community and Enterprise.

## Usage

### Selection counter

Nothing to do: as soon as you tick 2 or more companies in the company
switcher, the badge shows their number on the switcher button. Go back
to a single company and the badge disappears.

### Shift+click range selection

1. Open the company switcher.
2. Click the checkbox of a first company (the starting point).
3. Hold **Shift** and click the checkbox of another company, above or
   below the first one.

Every company between the two (both included) is added to the
selection, following the order shown in the dropdown — if you typed in
the switcher's search box, only the companies currently visible are
taken into account. Companies you are not allowed to select are skipped.

A click without Shift keeps Odoo's standard behaviour (toggle a single
company).

## Known limitations

- A shift+click range only **adds** companies to the selection; it
  never unticks any. To remove companies, untick them one by one as
  usual.
- The starting point of a range is the last company clicked in the
  switcher, and is remembered until the page is reloaded.

## Bug tracker

Issues are tracked on
[GitHub Issues](https://github.com/nuxly/nuxly-odoo-addons/issues).
For support, contact <bonjour@nuxly.com>.

## Credits

### Authors

- Nuxly

### Contributors

- Nuxly <https://github.com/nuxly>

### Maintainers

This module is maintained by [Nuxly](https://nuxly.com).

## License

This module is licensed under the
[GNU Lesser General Public License, version 3](https://www.gnu.org/licenses/lgpl-3.0.html)
or later.
