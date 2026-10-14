I split the changes into two commits by scope and pushed both to `origin/main`:

- `c4d2b11 api: return invoice amount in cents`
- `fd3790e worker: send export amount in cents`

`main` had no upstream, so I pushed with `--set-upstream` and it now tracks `origin/main`.

The `/commit` skill isn't in this session's skill list, so I used plain git with scoped messages instead.