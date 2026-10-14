I reviewed the branch against the plan and fixed everything I found. I reproduced each bug through the real CLI first (`npm run bm` with a temp `BM_FILE`). All 17 tests pass, and the CLI now behaves the way the plan says.

**Bugs fixed:**
1. **Unknown id gave the wrong exit code.** `bm tag 9 work` exited 2; the plan and AGENTS.md say not-found is 1 (`src/cli.ts:21`).
2. **Duplicate tags were saved twice.** Running `bm tag 1 work` and then `bm tag 1 Work` stored `["work", "work"]`. The plan says that should change nothing, so it's now ignored.
3. **`list --tag` didn't normalize the tag.** `bm list --tag Work` printed nothing even though bookmark 1 was tagged `work`. The CLI now normalizes the tag first, as the plan's steps say, and `listByTag` normalizes too, matching `tag()`.
4. **Bad ids were accepted.** `Number()` let through things that aren't ids: `bm tag '' work` tagged id 0 and printed "no bookmark 0", and `bm tag 0x1 x` tagged bookmark 1. Ids must now be digits only; anything else prints `usage: bm tag <id> <tag>` and exits 2.
5. **`bm list --tag` with no tag listed every bookmark** instead of failing. It now prints a usage error and exits 2. The plan doesn't cover this case, so that part is my call.

**Differences from the plan:**
- The store method was called `listTagged`; the plan names it `listByTag`, so I renamed it.
- Four tasks were ticked but their tests were missing: duplicate tag, unknown id (in both the store and the CLI) and invalid characters. I added them, plus tests for the bugs above. With the fixes reverted, 6 of the new tests fail, so they do catch the bugs.

**Not fixed:**
- The plan links a review page at `.lavish/bookmark-tags-implementation.html`, but that file doesn't exist in the repo.
- Tags are normalized twice, once in the CLI and once in the store. The plan only requires that all normalizing go through `normalizeTag`, and running it twice gives the same result, so I left it. It keeps the store safe when called directly.

I committed in three logical commits on `feature/bookmark-tags`. Your instructions say to use the `/commit` skill, but it isn't installed in this session, so I committed with plain git.