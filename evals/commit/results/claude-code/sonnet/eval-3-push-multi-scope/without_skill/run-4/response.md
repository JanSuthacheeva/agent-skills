I split the changes into two commits by scope and pushed them to `origin/main`:

- `378346a` api: return invoice amount in cents
- `93e31b7` worker: send export amount in cents

The first plain `git push` failed because `main` had no upstream. I re-ran it with `--set-upstream origin main`, so `main` now tracks `origin/main`.

The `/commit` skill your instructions call for isn't in my skill list, so I wrote the commits by hand in the `<scope>: <description>` format.