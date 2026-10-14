Bookmark tags are finished on `feature/bookmark-tags`: `bm tag <id> <tag>` and `bm list --tag <tag>` work. All 16 tests pass, and I ran the real CLI against a temp store file. Nothing is pushed.

**Commits**
- `86d79ff bm: store tags on bookmarks`: new bookmarks get an empty tag list, and older store files load as having no tags, so no migration is needed.
- `7ec345d bm: tag bookmarks and list them by tag`: tagging an unknown id raises a not-found error, and adding a tag twice does nothing.
- `7652ed8 bm: add tag command and list --tag`: the two commands, plus their error messages and exit codes.
- `562f642 docs: mark bookmark tags plan done`: ticks the last checkbox in the plan.

**What I saw running the CLI:** I started from a store file written before tags existed. `add`, `tag` and `list --tag RUNTIME` gave the expected output, and tagging bookmark 2 twice left one `runtime` tag. The error cases matched the plan:

| Command | Output | Exit |
|---|---|---|
| `bm tag 9 work` | `no bookmark 9` | 1 |
| `bm tag 2 "to do"` | `invalid tag: to do` | 2 |
| `bm tag x work` | `usage: bm tag <id> <tag>` | 2 |

**Changes from the plan:** one, which the plan doesn't cover. `bm list` with any argument other than `--tag <tag>` now prints `usage: bm list [--tag <tag>]` and exits 2; before, it ignored extra arguments. I added this to the plan's error list. If you'd rather keep ignoring extra arguments, it's a two-line change.

**Not checked:** the project has no linter or type checker. Node only strips the types, so the type annotations have never actually been checked.

**How it works:** `src/main.ts` calls `run` in `src/cli.ts`, which reads the command and cleans up the tag with `normalizeTag` (trim, lowercase, then check for `a-z`, `0-9` and `-`). It then calls `BookmarkStore.tag` or `listByTag` in `src/store.ts`, which read and write the JSON file. Errors are caught in one place in `run` and turned into a message and exit code: 2 for an invalid tag, 1 for an unknown bookmark.