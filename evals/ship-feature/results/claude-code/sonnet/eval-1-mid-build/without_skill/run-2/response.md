The bookmark tags feature is built and committed on `feature/bookmark-tags`, and all five plan tasks are checked off. All 20 tests pass, and I ran the real CLI against a temp store file.

The CLI run covered these cases:
- **Tagging:** `bm tag 2 " Work"` printed `tagged 2 work`. Tagging again with the same tag did nothing.
- **Filtering:** `bm list --tag WORK` listed only bookmark 2.
- **Errors:** an invalid tag exits 2, an unknown id exits 1, and bad usage exits 2.

This session's commits:
- `ca8481d` adds `tags` to bookmarks. Old store files without a `tags` field load as empty.
- `56fa246` adds `BookmarkNotFoundError`, `BookmarkStore.tag` and `BookmarkStore.listByTag`.
- `28d479f` adds `bm tag <id> <tag>` and `bm list --tag <tag>`.
- `67c9085` marks the plan done.

- **Plan deviation:** the store also normalizes tags itself, not just the CLI, so no caller can save an invalid tag. The CLI still normalizes first, as the plan says, because it needs the normalized tag for its output.
- **Extra usage message:** `bm list --tag` with no value prints `usage: bm list [--tag <tag>]`. The plan didn't specify that case.
- **Branch not reviewed:** I haven't run `/review-changes` or opened a merge request. Say if you want either.