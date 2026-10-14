The bookmark tags feature is built: `bm tag <id> <tag>` and `bm list --tag <tag>` both work. All 18 tests pass and the working tree is clean. The project has no lint or type-check setup, so only the tests were run.

**Tasks and commits** (task 1 was already done):
- `5f741c2` adds `tags` to `Bookmark`. New bookmarks start with `tags: []`, and old store files load with empty tags, so no migration is needed.
- `5b84e40` adds `BookmarkNotFoundError`, `BookmarkStore::tag` and `BookmarkStore::listByTag`.
- `8106b78` adds the `tag` command and `list --tag` to `run`.
- The last commit ticks the end-to-end task in the plan.

**Deviations from the plan:**
- I added one usage error the plan didn't specify: `list --tag` with no value, or any other list option, prints `usage: bm list [--tag <tag>]` and exits 2. A missing tag in `bm tag` shows the existing `usage: bm tag <id> <tag>`. I added both to the plan's error list.
- For the store tasks I wrote the tests and the code together and never ran the tests red first. The CLI task followed the red-then-green order.

**End-to-end check:** against a temp store file, I ran the real CLI and saw this:
- Adding, tagging and `list --tag runtime` worked.
- Tagging the same tag twice was a no-op.
- `"Runtime"` was stored as `runtime`.
- An invalid tag, an unknown id, a non-numeric id and a bare `--tag` gave the messages and exit codes the plan lists (2, 1, 2 and 2).
- The store file has `tags` on each bookmark.

**How it works:**
- `main` calls `run(argv, store, out)`.
- `run` calls `dispatch`, which normalizes the tag with `normalizeTag` and then calls `BookmarkStore::tag` or `listByTag`.
- `tag` loads the bookmarks, adds the tag if it isn't already there, and saves.
- `run` turns `InvalidTagError` and `BookmarkNotFoundError` into the messages and exit codes.

I haven't pushed anything or opened a merge request. `review-changes` or `write-merge-request` are the next steps if you want them.