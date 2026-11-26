I found and fixed five places where `feature/bookmark-tags` didn't match the plan. All 16 tests pass at `b6dc010`. The repo has no lint or type checker set up, so neither ran.

**Fixed** (each has a test that fails without the fix):
- **Duplicate tags:** tagging a bookmark with a tag it already had stored it a second time (`["work","work"]`). The plan says tags have no duplicates and re-tagging does nothing. Fixed in `e8e7297`.
- **Method name:** the store method was called `listTagged`; the plan calls it `listByTag`. Renamed in `6d113e0`.
- **CLI fixes** (all in `b6dc010`):
  - An unknown id in `bm tag` exited with 2 instead of 1.
  - `bm tag "" work` read the empty id as 0 and printed `no bookmark 0` instead of the usage message.
  - `list --tag` didn't clean up its tag, so `--tag Work` didn't find bookmarks tagged `work`. An invalid tag printed an empty list and exited 0 instead of `invalid tag: …` with exit 2.
- **Missing tests:** I added the ones the plan asked for: a duplicate tag, an unknown id (store and CLI), and a non-numeric id.

**Open, for you to decide:**
- **`bm list --tag` with no value** lists every bookmark and exits 0. The plan doesn't cover this. I'd make it a usage error.
- **Stricter ids:** ids must now be plain digits, so `" 1"` and `1.0` give the usage error. Before, they tagged bookmark 1. That fits the plan's "non-numeric id" rule.
- **Normalizing in the store:** `BookmarkStore.tag()` cleans up the tag again after the CLI already has, but `listByTag()` doesn't. It's harmless, but the two methods behave differently.

**Where to look:**
1. `src/store.ts`, `load()` → `tag()` → `save()`: how old files without tags load, and re-tagging now skips the save.
2. `src/cli.ts` `run()`: how errors map to exit codes.
3. The `list` case in `src/cli.ts`.

You can skim the rest.

**Checks:**
- **Security:** `/security-review` found nothing.
- **Fix review:** a separate agent checked the three fix commits. They hold, and its only notes are the stricter ids above and a garbled `no bookmark` message for ids above 2^53.

This summary is also in the plan as a `## Review` section (`96b4aaf`). Nothing has been pushed.