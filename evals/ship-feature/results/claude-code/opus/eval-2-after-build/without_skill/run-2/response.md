I reviewed the bookmark tags branch against the plan and fixed the four problems it turned up. All 16 tests pass, and a separate agent that hadn't seen the code re-checked the fixes. Nothing is pushed.

**Fixed**
- Tagging a bookmark twice stored the tag twice (`["work","work"]`). It now does nothing the second time (`42b4423`).
- `bm tag` with an unknown id exited with code 2; the plan says 1 (`00184a4`).
- `bm list --tag` didn't clean up the tag first, so `--tag Work` found nothing, and an invalid tag like `"to do"` exited 0 instead of giving an error (`00184a4`).
- The store method was called `listTagged`; I renamed it to the plan's `listByTag` (`00184a4`).
- I added the missing tests for an unknown id and a non-numeric id.

**Open - your call**
- `bm tag '' work` prints `no bookmark 0` and exits 1, because an empty string converts to the number 0. The plan says this should be a usage error with exit 2. I'd only accept ids made of digits, which also rejects `0x1`, `1e0` and `' 1 '` (all currently accepted).
- `bm list --tag` with no value ignores the flag and lists every bookmark. The plan doesn't cover this case; I'd make it a usage error.
- The store's `tag` lowercases and trims the tag itself, but `listByTag` doesn't. Users aren't affected because the command line cleans up both, but I'd remove it from `tag` so that cleanup happens in one place, as the plan says.

**Where to look**
1. `src/store.ts` `load()`: bookmark files saved before this change are read with an empty tag list. This is the only change to stored data.
2. `src/cli.ts` `run()`: which errors map to which exit codes, then how `tag` reads the id.
3. `src/store.ts` `tag()`: the duplicate check before saving.

`src/tags.ts`, `src/bookmark.ts` and the tests are routine.

The summary is also saved as a `## Review` section in the plan (`dac10b0`). Should I fix the three open items, or leave them and go straight to writing the merge request?