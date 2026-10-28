I found the cause of SHOP-313 and wrote a fix plan. I haven't changed any code, and the reporter's guess is wrong: `bm tag` does use the id.

**Root cause:** at `src/store.ts:38`, bookmarks saved before the update have no `tags` field. When the file is loaded, every one of them gets the same array, `noTags` (`src/store.ts:18`). So when `tag()` adds a tag to bookmark 3 (`src/store.ts:75`), it adds it to that one shared array, and saving writes the tag to every old bookmark. This came in with ad2332a "bm: tag bookmarks and list by tag".

**Evidence:**
- **Reproduction:** I created a bookmarks file with the version before tags (6978043), then ran `bm tag 3 recipes` with the current version. `bm list --tag recipes` listed all 5 bookmarks, and the file had `"tags": ["recipes"]` on each one. It fails every time.
- **Control:** with a file created only by the current version, tagging works correctly. The bug needs records without a `tags` field.
- **Experiment:** I loaded a file with two records without tags and one with `"tags": []`. The two without tags had the identical array (`===` was `true`); the third did not (`false`).
- **Why the tests missed it:** the test "bookmarks saved before tags load with no tags" creates its bookmark with `add()`, which already saves `tags: []`. No test ever loaded a record without tags.

**Also affected:** no other code changes tags today. The real damage is in users' data: anyone who tagged a bookmark in an old file now has that tag saved on all their old bookmarks. The fix (`record.tags ?? []` instead of the shared array) stops new damage but doesn't remove those tags. We also can't reliably tell which tags a user really set.

**Plan:** `docs/plans/2026-10-27-fix-tag-spreads-to-all-bookmarks.md`. It's the only change in the working tree, and nothing is committed.

**Decisions for you:**
1. Should the fix also repair tags already saved wrongly? I recommend not doing it automatically, because the real tags can't be told apart from the spread ones. Instead, tell the reporter and note it in the release notes. There's no `untag` command yet, so for now the cleanup would mean editing the file by hand.
2. Should we add a `bm untag <id> <tag>` command for cleanup? I recommend yes, but as a separate ticket, since it adds a new public command.