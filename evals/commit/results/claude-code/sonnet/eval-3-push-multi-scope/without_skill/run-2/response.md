I split the change into two commits by scope and pushed both to `origin/main`:

- `c2a765c api: return invoice amount in cents`
- `3d52a33 worker: send export amount in cents`

The `/commit` skill isn't available in this session, so I made the commits by hand.

The first push failed because `main` had no upstream branch. I re-ran it with `-u`, so `main` now tracks `origin/main`.