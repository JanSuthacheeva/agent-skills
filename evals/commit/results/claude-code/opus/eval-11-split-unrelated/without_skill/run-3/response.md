I committed the changes as three separate commits because they weren't related to each other. The working tree is now clean.

- `57b2720 billing: use banker's rounding for invoice totals`
- `79dd822 worker: increase export retries to 5`
- `7ca9927 docs: describe service in readme`

Your instructions say to use the `/commit` skill, but it isn't installed here, so I wrote the messages by hand in the repo's `<scope>: <description>` format.

The rounding change affects money: amounts that end in exactly half a cent can now total one cent less than before. For example, `0.125` used to round to `0.13` and now rounds to `0.12`. If that isn't what you meant, the billing commit is the one to revisit.