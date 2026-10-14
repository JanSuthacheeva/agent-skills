I reviewed the branch against the plan and fixed everything I found. Before fixing, I reproduced each bug through the real CLI (`npm run bm` with a temp `BM_FILE`). Tests now pass 16 of 16. The 6 new tests that cover the bugs fail when run against the original source, so they do catch them. Everything is committed as `514d2c5` with plain git, because the `/commit` skill isn't available in this session.

**Bugs fixed**
1. **Duplicate tags:** running `bm tag 1 work` twice stored `["work", "work"]`. The plan says re-tagging should do nothing, so it now does nothing (`src/store.ts:50`).
2. **Wrong exit code for an unknown id:** it exited 2, but the plan and AGENTS.md say "not found" is exit 1. It now exits 1 (`src/cli.ts:21`).
3. **`list --tag` didn't normalize the tag:** `bm list --tag Work` printed nothing, even though `bm tag 1 Work` stores the tag as `work`. The CLI now runs the tag through `normalizeTag`, as the plan says.
4. **`list --tag` with no value listed every bookmark** without complaint. It now prints `usage: bm list [--tag <tag>]` and exits 2. Extra arguments get the same error.
5. **Bad ids read as 0:** `Number("")` is 0, so `bm tag "" work` printed `no bookmark 0`. Ids must now be digits, otherwise the usage error and exit 2.

**Differences from the plan, fixed**
- The plan names the method `listByTag`, but the branch called it `listTagged`. I renamed it.
- All five plan tasks are ticked, but the tests the plan asks for were missing: duplicate tag, unknown id (in both store and CLI tests) and non-numeric id. I added them, plus tests for the `list --tag` fixes and an invalid-character case for `normalizeTag`.

The plan links a review page at `.lavish/bookmark-tags-implementation.html`, but that file isn't in the repo. I left the link as it is.