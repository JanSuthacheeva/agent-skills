The bookmark tags feature is reviewed and fixed. I haven't pushed or opened a merge request, so say if you want that next. All 16 tests pass.

All plan tasks were already done, so I ran the review. The review found these problems against the plan, and I fixed them in `9ee3c1c`, each with a failing test first:
- **Exit code:** `bm tag` with an unknown id exited 2, but the plan says 1.
- **Duplicate tags:** tagging twice stored the tag twice, but the plan says it's a no-op.
- **Tag filter:** `list --tag Work` found nothing, and `list --tag "to do"` wasn't rejected. The CLI now normalizes and validates the filter.
- **Naming:** `listTagged` is now `listByTag`, as the plan says.
- **Missing tests:** I added tests for the unknown id, the duplicate tag and a non-numeric id.

A fresh agent reviewed the fix commit and found no problems.

Two small things are left open, and I recorded both in the plan's `## Review` section (`62f41a1`):
- `bm list --tag` with no value lists everything instead of printing usage. I recommend a usage error with exit 2.
- `bm tag "" x` reads the empty id as 0 and reports `no bookmark 0`. I recommend rejecting empty ids as usage.

To review it yourself, read `src/store.ts` `load()` first. Old store files get empty tags in memory and are only rewritten on the next save. Then read the `run()` error mapping and the `tag` and `list` cases in `src/cli.ts`. `src/tags.ts` and the tests are routine.