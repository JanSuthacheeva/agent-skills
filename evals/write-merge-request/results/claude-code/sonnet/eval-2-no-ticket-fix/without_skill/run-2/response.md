I pushed `fix/line-rounding` and opened the MR against `main`: https://gitlab.com/shop/shop/-/merge_requests/57

- **Title:** `billing: round totals per line instead of per invoice`. The branch name has no ticket ID, so I used the scoped-commit format.
- **Description:** it covers why (invoice totals drifted from the PDF by up to a cent, and the accounting export rejected them), what changed (each line is rounded before summing), and a note that totals can shift by a cent on invoices with fractional line amounts.
- **Tests:** the MR adds none, and the description says so.