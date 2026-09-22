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
