The review is done and checked in the repository. It added 4 commits (3 fixes plus the `## Review` section), and all 16 tests pass. It left two open items, and the flow stops here until you decide them.

**1. `bm list --tag` with no value** currently lists every bookmark and exits 0.
- **Option A (recommended):** print `usage: bm list [--tag <tag>]` and exit 2. This matches how `tag` handles bad arguments, and right now a typo silently gives a wrong result.
- **Option B:** keep the current behaviour.

**2. Who normalizes tags.** `BookmarkStore::tag` normalizes the tag again after the CLI already has, but `listByTag` expects a tag that is already normalized.
- **Option A (recommended):** the caller normalizes and the store accepts only normalized tags, so the extra normalizing in `tag()` goes. That's what the plan already says: tags are "normalized once", the CLI calls `normalizeTag` before the store, and the store owns tagging rather than validation.
- **Option B:** the store normalizes in both `tag()` and `listByTag()`, which is safer if anything else ever calls the store.

Shall I go with A for both? I'll add them as tasks to the plan, commit, and run another build and review before the merge request.