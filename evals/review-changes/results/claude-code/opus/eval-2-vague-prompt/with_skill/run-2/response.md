I reviewed the branch against the plan and fixed four bugs, each in its own commit with a test written first. All 16 tests pass (10 before), the CLI behaves correctly on a real store file, and a fresh agent reviewed the three fix commits and found no problems.

**Fixed**
- **Duplicate tags were saved:** running `bm tag 1 work` and then `bm tag 1 Work` wrote `["work","work"]` to the file. The plan says repeating a tag does nothing. Fixed in `b587dd9`.
- **Unknown id had the wrong exit code:** `bm tag 9 work` exited 2, but the plan and `AGENTS.md` say 1 for "not found". Also, `bm tag "" work` printed "no bookmark 0" instead of the usage message. Fixed in `50267fa`.
- **`list --tag` didn't normalize the tag:** `bm list --tag Work` found nothing, and `bm list --tag "to do"` exited 0 instead of rejecting it with exit 2. I also renamed `listTagged` to `listByTag` to match the plan. Fixed in `d2dc0f0`.
- **Missing tests:** the plan asked for tests for a duplicate tag and for an unknown id, at both the store and the CLI level. They're now added, in the same commits.

**Open**
- **`bm list --tag` with no value** quietly lists every bookmark and exits 0. The plan doesn't cover this case, and fixing it changes what users see. I recommend printing `usage: bm list [--tag <tag>]` and exiting 2.
- **Type checks and lint:** the project has neither set up, so I only ran the tests.

**Where to look**
1. `src/store.ts` `load()` to `tag()`: how files saved before tags existed get `tags: []`, and the new duplicate check before `save()`.
2. `src/cli.ts` `run()`: how errors map to exit codes (invalid tag gives 2, not found gives 1).
3. `src/cli.ts` the `list` case: how `--tag` is parsed, including the open question above.

`src/tags.ts`, `src/bookmark.ts` and the plan checkbox edits are routine and can be skimmed. Nothing has been pushed.