I reviewed the branch against the plan, fixed four deviations, and committed the fixes as `b3cd3b0`. All 14 tests pass. I also ran `add`, `tag` and `list --tag` against a temp store file, and the output matched the plan.

What I found and fixed:
1. **Duplicate tags:** `BookmarkStore.tag` pushed a tag even if the bookmark already had it. The plan says tagging again is a no-op, so it now skips the push and the save in that case.
2. **Method name:** the store method was `listTagged`, but the plan names it `listByTag`. I renamed it.
3. **Exit code:** an unknown id in `bm tag` exited 2, and the plan says 1. It now exits 1.
4. **Tag not normalized in `list --tag`:** the CLI passed the raw tag to the store, so `list --tag Work` found nothing. `run` now calls `normalizeTag` first, as the call chain specifies.

I added tests for the gaps the plan's task list called for: a duplicate tag, an unknown id (store and CLI), and `list --tag` normalization.

Three things you may want to look at:
- `bm list --tag` with no value still lists everything. The plan doesn't cover it, so I left it.
- `list --tag` with an invalid tag throws `InvalidTagError`, so it prints `invalid tag: <raw>` and exits 2. That follows the plan's error rules, but I didn't add a test for it.
- The `/commit` skill wasn't available in this session, so I used plain `git commit`.