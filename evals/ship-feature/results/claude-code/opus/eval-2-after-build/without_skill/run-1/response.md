I reviewed the bookmark tags branch against its plan and fixed six problems that broke what the plan says. All 16 tests pass, and I checked the fixed behaviour by running the real CLI. Nothing is pushed.

**Fixed:**
- **Duplicate tags:** tagging a bookmark twice saved the tag twice in the file. Re-tagging now does nothing, as the plan says. (f6ae3b7)
- **Method name:** the store method was called `listTagged`; it's now `listByTag`, the plan's name. (2bb024f)
- **Unknown id:** `bm tag 9 work` exited with code 2 instead of 1. (9c2dff2)
- **Bad ids:** an empty or hex id was read as a number, so `tag '' work` printed `no bookmark 0` instead of the usage message. (9c2dff2)
- **`list --tag` ignored normalization:** `--tag Work` found nothing, and an invalid tag like `'to do'` exited 0 instead of 2. (9c2dff2)
- **Missing tests:** added the ones the plan asked for: duplicate tag, unknown id (store and CLI), non-numeric id, and `list --tag` normalizing and rejecting tags.

A separate agent reviewed the fix commits. It confirmed each fix, and that each has a test that fails without it.

**Open, for you to decide:**
- **`bm list --tag` with no value** lists every bookmark and exits 0. The plan doesn't cover this. I recommend printing `usage: bm list [--tag <tag>]` and exiting 2, and treating any other unknown `list` argument the same way. I left it because it changes how the command behaves for users.
- **Negative ids:** `tag -1 work` now prints the usage message rather than `no bookmark -1`. Ids are always positive, so I'd keep it.
- **No lint or type check:** the project has neither, so only the tests catch type errors. I recommend adding `tsc --noEmit`.

**Where to look:**
1. `src/store.ts`, from `load()` through `tag()` to `save()`: how files saved before tags existed are read, and that a rejected tag never writes the file.
2. `src/cli.ts`, the catch block in `run()`: which errors map to which messages and exit codes.
3. `src/cli.ts`, the `list` case: where the open `--tag` item lives.

The rest (`src/tags.ts`, `src/bookmark.ts` and the tests) is routine and can be skimmed.

This summary is also saved as a `## Review` section in the plan (b7c5c3b). Should I fix the `list --tag` case as recommended, and then write the merge request?