The bookmark tags feature is built and all five plan tasks are done. All 19 tests pass, and I checked the real CLI against a temp store file.

**Commits** (I used plain `git commit` with your `bm:` and `docs:` prefixes, not the `/commit` skill):
- `bm: add tags field to bookmarks`: `Bookmark.tags`, new bookmarks start with `tags: []`, and `load()` reads old files without a `tags` field as `[]`.
- `bm: tag bookmarks and list by tag in the store`: `BookmarkNotFoundError`, `BookmarkStore.tag` and `BookmarkStore.listByTag`. Tagging with a tag the bookmark already has changes nothing.
- `bm: add tag command and list --tag`: `bm tag <id> <tag>` and `bm list --tag <tag>`.
- `docs: mark bookmark tags plan done`: ticks the last task in the plan.

**End-to-end run:**
- Tagging, then `list --tag RUNTIME`, matched the bookmark tagged `runtime`.
- Unknown id: `no bookmark 9`, exit 1.
- Invalid tag: `invalid tag: a b`, exit 2.
- Non-numeric id: usage message, exit 2.
- The store file is still a JSON array with the new `tags` field.

**Where I went beyond the plan:**
- **Tag-already-present message:** `tagged <id> <tag>` first used the last tag on the bookmark, which would be wrong when the tag already existed. The CLI now normalizes the tag and prints that, as the plan's call chain says, and a test covers it.
- **Usage error for `list --tag`:** `bm list --tag` with no value, or any other argument after `list`, now prints `usage: bm list [--tag <tag>]` and exits 2. The plan didn't specify this case.