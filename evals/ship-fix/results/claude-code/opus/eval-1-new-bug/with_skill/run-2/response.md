SHOP-311 is diagnosed and the fix plan is written. I need your approval before I build anything.

**Root cause:** `list --tag` isn't broken. `toRecord()` at `src/store.ts:26` leaves out `tags` when it turns a bookmark into what gets saved. Every `bm add` rewrites the file through `save()`, so it erases the tags of every bookmark. `tag()` only works because it adds the tags back itself at `src/store.ts:74`. The bug came in with 6d668ea, which added tags to loading but not to saving.

**Evidence:** I ran the real CLI against a scratch `BM_FILE` with these steps: add, add, `tag 1 work`, then `list --tag work`, which shows bookmark 1. Then `add` again, and `list --tag work` prints nothing. It fails every time. Looking at the file between steps shows `"tags": ["work"]` on disk after `tag`, and no `tags` field on any record after the next `add`.

**Also affected:** Users' own files are already damaged. Anyone who added a bookmark after tagging has lost those tags, and the file keeps nothing to restore them from. `add()` is the only other code path that writes the file, and the fix covers it.

**Plan:** `docs/plans/2026-10-27-fix-tags-lost-on-add.md`. It has two tasks:
1. A regression test in `test/store.tags.test.ts`, then add `tags` to `toRecord()` and have `tag()` save through `save()`.
2. Rerun the reproduction end to end.

**Open question:**
1. Tags that are already lost can't be recovered. Should we do anything beyond the fix? I recommend no repair: the merge request and a note on SHOP-311 would tell affected users to re-tag.

Do you approve the plan and that recommendation? Once you do, I'll create a `SHOP-311` branch and commit the plan there. Then please run `/compact` and say "continue fixing" to start the build.