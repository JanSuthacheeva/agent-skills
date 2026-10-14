I reviewed the bookmark tags branch: it had three bugs against the plan, all now fixed. All 15 tests pass, and an end-to-end run with the CLI against a temp store gives the right output and exit codes.

**Fixed**
- **Duplicate tags:** tagging a bookmark with a tag it already had added it again, so the store file ended up with `["work", "work"]`. It now does nothing, as the plan says. (a8d0017)
- **`bm tag` exit codes:** an unknown id exited 2 instead of 1. An empty id was read as 0 and printed `no bookmark 0` instead of the usage line. (4dc9697)
- **`bm list --tag` didn't clean up the tag:** `--tag Work` found nothing, and an invalid tag like `--tag "to do"` printed nothing and exited 0. I also renamed the store method from `listTagged` to `listByTag`, the name in the plan. (eb564de)

Each fix started with a failing test. A separate agent that saw only the three fix commits and what they fix re-checked them, including inputs like `01`, `" "`, `1.5` and differently-cased duplicate tags. It found nothing wrong.

**Open**
- `bm list --tag` with no value lists every bookmark without complaint. I'd make it print `usage: bm list [--tag <tag>]` and exit 2. I left it alone because it changes what users see and the plan doesn't cover it - your call.

**Where to look**
1. `src/store.ts`, from `load()` through `tag()` to `save()`: how files written before tags existed are read, and how the whole file is read and rewritten on every tag.
2. `src/cli.ts`: how errors become messages and exit codes in `run()`, and the `tag` and `list` cases. These are what users see.

The rest can be skimmed.

The review is written into `docs/plans/2026-10-14-bookmark-tags.md` as a `## Review` section (9e9672e). Nothing is pushed. The next step would be the merge request - tell me if you want me to write it, or to fix `list --tag` first.