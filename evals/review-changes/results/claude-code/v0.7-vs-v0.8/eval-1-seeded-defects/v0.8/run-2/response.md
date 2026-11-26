I found four places where the branch didn't match the plan and fixed each in its own commit, with a test that fails without it. All 20 tests pass now. The project has no lint or type-check script, so the tests are the only check.

**Fixed**
- **Duplicate tags saved:** tagging the same bookmark with `work` twice stored `["work","work"]`. The plan says tags have no duplicates and re-tagging does nothing; now it does nothing. I also renamed `listTagged` to `listByTag`, the name the plan uses. `25957b0`
- **Wrong exit code for an unknown id:** `bm tag 9 x` exited 2; the plan and `AGENTS.md` say 1 for "not found". `184d603`
- **`list --tag` didn't normalize the tag:** `--tag Work` found nothing, and an invalid tag like `"to do"` exited 0 instead of printing `invalid tag`. `c56d224`
- **Bad ids got past the usage check:** `bm tag "" x` printed `no bookmark 0`, and `0x1` was read as id 1. Any id that isn't a plain number now prints the usage message and exits 2. `f0d13f2`
- I added the tests the plan asked for that were missing: a duplicate tag, an unknown id, `list --tag`, and non-numeric ids.

**Open, for you to decide**
- `bm list --tag` with no value quietly lists every bookmark. The plan doesn't say what should happen. I'd print a usage error and exit 2, but that changes behaviour users see, so I left it.
- If someone hand-edits the bookmarks file so `tags` isn't a list, `tag` and `list --tag` crash with a `TypeError`. That's low risk, since it's the user's own file.
- The plan links a review page, `.lavish/bookmark-tags-implementation.html`, that doesn't exist in the repo.

**Where to look:** `src/store.ts` from `load()` through `tag()` to `save()` (how old files without tags load, and that re-tagging doesn't write), then `run()` in `src/cli.ts` (exit codes and argument parsing). The rest is routine.

The security review on `main...HEAD` found nothing. A separate agent reviewed the four fix commits and found no problems.

I wrote this summary into the plan as a `## Review` section (`69b9576`). Nothing has been pushed.