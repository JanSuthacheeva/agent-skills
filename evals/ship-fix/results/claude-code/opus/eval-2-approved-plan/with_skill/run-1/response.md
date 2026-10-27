The SHOP-311 fix is built and reviewed on `fix/SHOP-311-tags-lost`. Before I write the merge request, I need your decision on two points the review left open.

**Build:** the cause was the one the plan named.
- **Task 1** (`867fcbb`): I wrote the regression test first, and it failed with `[]` instead of `[ 'work' ]`, as the plan predicted. The fix is that `toRecord()` now copies `tags`, so `bm add` no longer rewrites the file without them.
- **Task 2** (`023d7eb`): `tag()` now writes through `save(all)` like `add()`, so there's only one place the file gets written. A new test checks that tagging two bookmarks keeps both tags.
- **Task 3** (`f06f525`): I ran the reproduction again, and the last `list --tag work` now prints `1  A  https://a.example`. All 17 tests pass. The project has no lint or type-check script.

**Review:** done in a separate agent that didn't see this conversation. It changed no app code. It fixed one test (`f59970b`): the old-file test no longer read a file saved before tags existed, so it would have passed even if loading those files broke. It now writes such a record itself.

**Open items:**
1. **Tags already lost can't be restored.** Every `bm add` since tags were introduced wiped all tags from the user's file. *Recommendation:* say so in the merge request and release notes so users know to tag again. No code change.
2. **The stored format changed slightly.** Every record now gets a `tags` field, `[]` when untagged. `tag()` already wrote files that way, and old files without the field still load, so no migration is needed. *Recommendation:* accept it.

Shall I go with both recommendations? Neither needs a code change, so the next step would be drafting the merge request. I won't push or open it until you say so.