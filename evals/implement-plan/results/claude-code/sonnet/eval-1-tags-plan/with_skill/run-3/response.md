Bookmark tags are implemented: `bm tag <id> <tag>` and `bm list --tag <tag>` both work. All 21 tests pass, and I ran the real CLI against a temp store file. The project has no lint or type-check script, so I ran neither. I used plain `git commit` because there is no `/commit` skill in this repo.

**Tasks and commits**
1. `1bc5956` - `normalizeTag` and `InvalidTagError` in `src/tags.ts`.
2. `2fd2f5b` - `Bookmark.tags`; `add` creates `tags: []`, and `load()` reads a missing `tags` field as `[]`.
3. `ec8dd71` - `BookmarkNotFoundError`, `BookmarkStore.tag` and `listByTag`.
4. `eb99bab` - the `tag` command and `list --tag` in `run`.
5. `b757eea` - end-to-end check done, last checkbox ticked.

**End-to-end check**
- **Adding and tagging:** I ran `add` twice, then `tag 2 ' Work '`, which printed `tagged 2 work`. Tagging with `work` again also printed `tagged 2 work`, exit 0, and the stored file shows the tag only once.
- **Filtering:** `list --tag WORK` printed only `2  B  https://b.dev`, and `list --tag none` printed nothing.
- **Errors:**

| Command | Output | Exit |
|---|---|---|
| `tag 2 'a b'` | `invalid tag: a b` | 2 |
| `tag 9 x` | `no bookmark 9` | 1 |
| `tag x y` | `usage: bm tag <id> <tag>` | 2 |

**Deviations from the plan**
- **Error handling:** `run` is now a thin wrapper that catches `InvalidTagError` and `BookmarkNotFoundError`, and the old body moved into a private `dispatch`. This keeps error-to-exit-code mapping in one place. The public `run(argv, store, out)` signature is unchanged.
- **Messages:** the two error classes build their own messages (`invalid tag: <raw>`, `no bookmark <id>`), and the CLI prints them as they are.
- **Gap in the plan:** `list --tag` with no value prints `usage: bm list [--tag <tag>]` and exits 2. The plan didn't cover this case, so I picked it. A missing tag on `bm tag <id>` falls under the existing `tag` usage message.

Nothing is blocked, and I haven't pushed anything.

**How it works**
- **Entry:** `main.ts` calls `run(argv, store, console)`, which delegates to `dispatch`.
- **Parsing and validation:** for `tag` and `list --tag`, `dispatch` validates the arguments and normalizes the tag with `normalizeTag`. This accepts only `a-z`, `0-9` and `-` after trimming and lowercasing.
- **Storage:** `BookmarkStore.tag` loads the bookmarks, appends the tag if it is new, and saves. `listByTag` filters the loaded bookmarks.
- **Old store files:** `load()` fills in `tags: []`, so existing store files work without a migration.