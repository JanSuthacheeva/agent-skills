I reviewed `feature/bookmark-tags` against its plan, fixed five places where the code didn't match it, and committed the fixes as `aed7684`. All 15 tests pass, and I ran the plan's last task (`add`, `tag`, `list --tag` against a temp store file) and the output was correct.

What I fixed:
- **Duplicate tags:** `BookmarkStore.tag` pushed the same tag twice. Tagging with a tag the bookmark already has is now a no-op.
- **Method name:** the store method was `listTagged`, but the plan calls it `listByTag`. I renamed it, and it now normalizes the tag it is given.
- **`list --tag` casing:** the CLI didn't normalize the tag, so `list --tag WORK` found nothing. It now normalizes.
- **`list --tag` with no value:** this silently listed every bookmark. It now prints `usage: bm list [--tag <tag>]` and exits 2.
- **Unknown id:** `tag` on an unknown id exited 2, but the plan says 1. It now exits 1.

I added tests for a duplicate tag, an unknown id (store and CLI), a non-numeric id, and `list --tag` with a differently-cased tag and with no value.

The `/commit` skill wasn't available in this session, so I committed with plain `git commit`.