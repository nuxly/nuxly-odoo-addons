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
