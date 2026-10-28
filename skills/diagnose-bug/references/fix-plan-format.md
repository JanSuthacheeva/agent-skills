# The fix plan

Read this in step 5. The plan is the only thing the build session sees,
so it has to stand on its own: the reproduction, the proven cause and the
tasks.

## Template

```markdown
# Fix: <what the user sees, in one line>

Report: <ticket id and title, or the report quoted>

## Report

Expected: <what the user expected>
Actual: <what happened instead>
Steps and environment: <as reported>

## Reproduction

<setup, then each command, request or action, then the observed output
quoted exactly; how often it fails>

## Root cause

<`file:line` where the state first goes wrong, the mechanism, the
experiment that proves it, and the commit that introduced it>

## Fix

<each unit that changes, by its name in the code, what changes in it and
why there and not where the symptom shows; every added or changed
signature, written out>

## Also affected

<the same mistake elsewhere; data already written wrong. "None found"
if you looked and found none.>

## Assumptions

- <a cheap-to-reverse choice made without the user>

## Open questions

1. <an expensive-to-reverse choice> - recommended: <answer>

## Tasks

- [ ] Add <test> in <file> (fails today with <message>), then fix <unit>
- [ ] <further tasks, only if the fix needs them>
- [ ] End-to-end: run the reproduction again and see <expected output>
```

Leave out `## Open questions` when there are none.

## Example

An illustration of the level of detail; the stack is incidental.

```markdown
# Fix: invoice total is one cent off the PDF

Report: BILL-88 "Export total doesn't match invoice"

## Report

Expected: the CSV export's total equals the invoice PDF's total.
Actual: for some invoices the export is one cent lower.
Steps and environment: export March invoices from the admin; production.

## Reproduction

    curl -s -X POST localhost:8000/api/invoices \
      -d '{"lines":[{"net":"0.105"},{"net":"0.105"},{"net":"0.105"}]}'
    # {"id":17}
    curl -s localhost:8000/api/invoices/17/pdf | pdftotext - - | grep Total
    # Total 0.33
    curl -s 'localhost:8000/api/exports?ids=17' | tail -1
    # 17,0.32

Fails every run for lines whose net has a third decimal.

## Root cause

`app/Billing/Totals.php:31` `Totals::forInvoice()` rounds the sum of the
lines once, while the PDF rounds each line (`app/Pdf/Invoice.php:58`), as
the tax office requires. Proven by calling `forInvoice()` on invoice 17 in
a scratch test: it returns 0.32 (0.315 rounded), while the three lines
rounded to 0.11 each sum to the PDF's 0.33. Introduced in 4e1d0aa
"billing: compute totals in one query".

## Fix

`Totals::forInvoice()` rounds per line, like the PDF, so both read one
rule. The export reads `forInvoice()`, so it follows without a change.

## Also affected

`Totals::forCustomer()` sums the same way. Exports written since 4e1d0aa
may be off by a cent; they are files the customer already has.

## Assumptions

- The regression test goes in `tests/Billing/TotalsTest.php`.

## Open questions

1. Re-send the exports written since 4e1d0aa? - recommended: no, list the
   affected invoices for accounting instead.

## Tasks

- [ ] Add "rounds per line" in `tests/Billing/TotalsTest.php` (fails today
  with `expected 0.33, got 0.32`), then fix `Totals::forInvoice()`
- [ ] Round per line in `Totals::forCustomer()`, with its test
- [ ] End-to-end: run the reproduction again and see `17,0.33` from the
  export
```
