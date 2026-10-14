All five plan tasks were already done, so I reviewed the branch. I found four bugs and fixed them, each with a test written first and its own commit. All 16 tests pass (up from 10). Nothing has been pushed.

**Fixed**
- **Duplicate tags:** tagging a bookmark twice saved the tag twice in the file, but the plan says tags have no duplicates. A repeated tag is now ignored (09eec76).
- **Wrong exit code:** `bm tag <unknown id>` exited 2 instead of 1, which the plan and `AGENTS.md` both reserve for "not found" (dda3500).
- **`list --tag` skipped tag cleanup:** `--tag Work` found nothing, and an invalid tag like `--tag "to do"` silently returned exit 0 instead of the `invalid tag` error. It now trims, lowercases and checks the tag like `bm tag` does (1f37c08).
- **Name mismatch:** renamed `listTagged` to `listByTag` as the plan specifies (9908a2e).
- Added the tests the plan asked for but were missing: duplicate tag, unknown id and non-numeric id.

A separate agent checked the three behaviour fixes against the real CLI and found them correct.

**Decisions for you**
- **`bm list --tag` with no value** ignores the flag and lists every bookmark with exit 0. I'd make it a usage error (exit 2). I left it because it changes how a command behaves for users.
- **Inconsistent tag cleanup in `src/store.ts`:** `tag()` cleans up the tag it's given but `listByTag()` doesn't. The CLI already does it before calling either, so I'd do it in both methods or neither.

The review summary and a reading order are in the `## Review` section of `docs/plans/2026-10-14-bookmark-tags.md` (52cf46a).

Next is the merge request. Tell me how to handle the two decisions, and whether I should go ahead and push and open it.