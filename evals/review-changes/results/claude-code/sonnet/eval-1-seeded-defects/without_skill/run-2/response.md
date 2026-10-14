I reviewed `feature/bookmark-tags` against the plan, fixed the deviations I found, and committed the fixes as `8d7d1d7`. All 16 tests pass. I also ran the CLI by hand against a temp store: `add`, `tag` (twice with the same tag), `list --tag`, and an unknown id.

**Deviations I fixed**
- **Method name:** the store had `listTagged`, but the plan specifies `listByTag`. I renamed it.
- **Duplicate tags:** `BookmarkStore::tag` pushed the tag again every time. The plan says tagging with an existing tag is a no-op, so it now skips the push and the save.
- **Unknown id exit code:** the CLI returned 2 for `BookmarkNotFoundError`. The plan and `AGENTS.md` say 1, so it now returns 1.
- **Tag normalization in `list --tag`:** the CLI passed the raw tag straight to the store, so `list --tag WORK` found nothing and an invalid tag was never rejected. The CLI now normalizes the tag (so an invalid one exits 2 with `invalid tag: <raw>`), and `listByTag` normalizes it as well.

**One addition beyond the plan:** `list --tag` with no value used to silently list everything. It now prints `usage: bm list [--tag <tag>]` and exits 2.

**Tests:** the plan's tasks require tests for a duplicate tag, an unknown id (store and CLI), and `list --tag`. Those were missing, so I added them. I also added tests for a non-numeric id and for normalization in `list --tag`.

**Left as is**
- **Review page:** the plan references `.lavish/bookmark-tags-implementation.html`, which doesn't exist in the repo. I didn't create it.
- **Task checkboxes:** the branch ticked every box in the plan, including the manual CLI check. That check wasn't backed by any test, though my manual run above covers it now.