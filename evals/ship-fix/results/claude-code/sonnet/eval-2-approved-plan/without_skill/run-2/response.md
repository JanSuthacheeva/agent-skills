SHOP-311 is fixed. The tests pass (17/17), and the reproduction from the plan now ends with `1  A  https://a.example` from the last `list --tag work`.

The bug was not in `list --tag`. `toRecord()` in `src/store.ts` left `tags` out, so every `bm add` rewrote the file without any tags.

I made three commits, each with `Refs: SHOP-311`:
1. **Regression test and fix:** the new test "adding a bookmark keeps existing tags" failed first, with `[]` instead of `['work']`. It passes once `toRecord()` copies `tags`.
2. **One write path:** `tag()` now saves through `save(all)`, and I removed the private `#write` helper. The new test "tagging two bookmarks keeps both tags" passed right after the first fix, so it guards this refactor rather than failing first.
3. **Plan:** I ticked off the tasks in `docs/plans/2026-10-27-fix-tags-lost.md`.

Every `bm add` since the tags commit wiped the tags in users' files, and they can't be recovered. They have to be re-added with `bm tag`. You may want to say so on the ticket. I haven't posted anything to ClickUp or changed the ticket's status.