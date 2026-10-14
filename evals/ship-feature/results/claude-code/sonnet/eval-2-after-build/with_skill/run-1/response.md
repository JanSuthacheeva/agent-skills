The review found open items, so the flow stops here for your decision.

**What the review fixed (3ba2066, each with a test that failed first):**
- `bm tag` on an unknown id now exits 1 instead of 2.
- Tagging the same tag twice is now a no-op.
- `list --tag` now normalizes and validates its tag, so `--tag Work` works and an invalid tag exits 2.
- `listTagged` is renamed to `listByTag`.
- The suite is at 15 of 15. The fix commit was re-read by the reviewer, not independently reviewed.

**Open items:**
1. **`bm list --tag` with no value** silently lists everything. I recommend a usage error, `usage: bm list [--tag <tag>]`, with exit 2. The plan doesn't cover it and it changes what users see, so this is your call.
2. **`load()` throws on a corrupt store file.** It was already like this, and nothing gets overwritten. I recommend skipping it.
3. **The final plan task** (run `add`, `tag` and `list --tag` against a temp store) is ticked, but nothing in the repo shows it was done. I'd run it myself before the merge request, and I don't need a decision for that.

**Where a human should look:**
1. `src/store.ts`, from `load()` through `tag()` to `save()`: the old-file format and the duplicate handling.
2. `src/cli.ts`, the `run()` catch block and the `tag` and `list` cases: exit codes and where normalization happens.

Should I add a task for item 1 (usage error, exit 2) and build it, then run the end-to-end check and move on to the merge request? Say if you want item 2 handled too.