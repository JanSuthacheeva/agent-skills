The review is done and I fixed four deviations from the plan. All 16 tests pass, and there is no lint or type-check script in the project. The branch is not pushed and no merge request is open.

**Fixed**
- **Duplicate tags:** a repeated tag was stored again, so a bookmark ended up with `work` three times. Tagging with an existing tag is now a no-op (`8f677f8`).
- **Store method name:** `listTagged` is now `listByTag`, as the plan names it (`8f677f8`).
- **Exit code:** tagging an unknown bookmark exited 2. It now exits 1, as the plan and `AGENTS.md` say (`99f9f36`).
- **`list --tag` input:** it did not normalize or validate its tag, so `Work` found nothing and `to do` exited 0. It now normalizes the tag and rejects an invalid one with exit 2 (`99f9f36`).

I wrote a failing test for each of these first. The fixes were not reviewed by an independent agent. I re-read them myself.

**Open**
- `bm list --tag` with no value silently lists everything. I recommend a usage error with exit 2. I left it alone because it changes user-visible behaviour.

**Mistake during the review:** my manual check ran without `BM_FILE` set, so it wrote to your real `~/.bookmarks.json`. It added bookmark 2 and two extra `work` tags on bookmark 1. I reverted those; the file now holds only bookmark 1 with a single `work` tag, which was already there before my run.

**Where to look:** `src/cli.ts` `dispatch` (the `tag` and `list` cases) for exit codes and messages, and `src/store.ts` `tag()` for the no-op rule. The tags module and the tests are routine. The review summary is also written into the plan under `## Review` (committed in the last commit on the branch).

If you want it, the next step is the merge request.