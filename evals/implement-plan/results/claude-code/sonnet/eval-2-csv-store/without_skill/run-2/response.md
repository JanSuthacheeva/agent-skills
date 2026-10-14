I implemented the plan and committed it as `f1abdec`. All 17 tests pass, and I ran `add`, `tag` and `list --tag` against a temp store file with the expected output. The one deviation is the store format, below.

**Deviation from the plan:** the plan says the store is a JSON array, but it is a CSV file (`.bookmarks.csv`). `store.ts` notes that users open it in spreadsheets and sync it, so the columns count as public format. I added `tags` as a trailing column, with tags joined by `;`. This works because tags can't contain `;` or `,`. The header is now `id,url,title,createdAt,tags`. Files written before this change load with `tags: []`, and older readers should ignore the extra column. If you'd rather not change the columns, tell me and I'll rework it.

**What changed:**
- `src/tags.ts`: new `normalizeTag` and `InvalidTagError`.
- `src/bookmark.ts` and `src/store.ts`: `Bookmark.tags`, `BookmarkNotFoundError`, `tag()` and `listByTag()`.
- `src/cli.ts`: the `tag` command and `list --tag`, with exit codes 2 for invalid input and 1 for an unknown id. `list --tag` with no value prints `usage: bm list [--tag <tag>]` and exits 2, which the plan didn't specify.
- Tests cover the new code, including loading a pre-tags file.
- I ticked the tasks in the plan file.

The `/commit` skill wasn't available in this session, so I committed with plain `git commit`.