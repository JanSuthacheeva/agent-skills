The bookmark tags feature is built: all five tasks in the plan are done and ticked off in `docs/plans/2026-10-14-bookmark-tags.md`. The tests pass (16, up from 6), and running the real CLI against a temporary store file gave the output and exit codes the plan specifies. The project has no lint or type checker set up, so neither was run.

**Commits:**
- `97aee6a bm: store tags on bookmarks` - new bookmarks start with no tags, and files saved before this change load with empty tags.
- `635214e bm: tag bookmarks and list them by tag` - adds the "not found" error and the store's `tag` and `listByTag`. Adding a tag a bookmark already has does nothing and doesn't rewrite the file.
- `3b520ce bm: add tag command and list --tag`
- `1702976 docs: tick bookmark tags end-to-end check`

**What I ran:** `add` twice; `tag 1 Work` printed `tagged 1 work`, and tagging it again changed nothing. `list --tag WORK` and `list --tag home` each showed only the matching bookmark. `tag 9 work` printed `no bookmark 9` (exit 1), and `tag 1 to-do!`, `tag x work` and `list --tag` each printed their error with exit 2. The store file kept its format, with a `tags` array added to each bookmark.

**Change from the plan:** the plan didn't cover `list` called with anything other than `--tag <tag>`, such as `list --tag` with no tag. That case now prints `usage: bm list [--tag <tag>]` and exits with 2, the same way `add` and `tag` handle bad input. It has a test and is written into the plan's errors list. This is a message users will see, so tell me if you want different wording.

**How it works:** `src/main.ts` passes the arguments to `run()` in `src/cli.ts`. That splits by command, checks the id format and normalizes the tag (`normalizeTag` in `src/tags.ts`: trims and lowercases). It then calls `BookmarkStore.tag` or `listByTag` in `src/store.ts`, which read and write the JSON file. `run()` catches the bad-tag and not-found errors and turns them into the messages and exit codes above.

Nothing is blocked. I haven't pushed or opened a merge request.