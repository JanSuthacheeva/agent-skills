Bookmark tags are built and work end to end: all 5 tasks in the plan are done and committed, and the full suite passes (20 tests, up from 4 before I started). There is no lint or type-check script in this repo, so tests were the only automated check.

**Commits**
1. `537c33f` - `normalizeTag` and `InvalidTagError` in `src/tags.ts`
2. `e152eac` - `Bookmark.tags`; new bookmarks get `tags: []` and old store files load as untagged
3. `d879743` - `BookmarkNotFoundError`, `BookmarkStore::tag` and `BookmarkStore::listByTag`
4. `19bfcde` - the `bm tag <id> <tag>` command and `bm list --tag <tag>`
5. `052ac0e` - ticks the last checkbox after the end-to-end check

The `/commit` skill isn't installed here, so I committed with plain git in the repo's `bm:` style. Nothing is pushed.

**End-to-end check:** I ran the real CLI against a temp store file that started in the old format, with no `tags` field:
- `bm tag 2 " Runtime "` printed `tagged 2 runtime`.
- Tagging a bookmark with a tag it already has did nothing and still succeeded.
- `bm list --tag RUNTIME` listed only the two tagged bookmarks.
- The error cases gave the planned messages and exit codes: `invalid tag: to read` (exit 2), `no bookmark 9` (exit 1), and the usage message for a non-numeric id (exit 2).
- The old bookmark was saved back with `tags: []`.

**Where I departed from the plan** (the plan file is updated to match):
- **`InvalidTagError`:** the plan wrote it as `constructor(readonly raw: string)`. AGENTS.md doesn't allow that shorthand, and Node 22 refuses to run it (I checked: `ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX`). I declared `raw` as a normal field and set it in the constructor; nothing visible changes.
- **New error cases the plan didn't cover:** `bm tag <id>` with no tag now gives the existing `usage: bm tag <id> <tag>` message. `bm list --tag` with no tag gives a new `usage: bm list [--tag <tag>]` message, exit 2.
- **Decision for you:** that list check also means any other extra argument to `list` (e.g. `bm list foo`) is now a usage error, where before it was silently ignored. It's easy to undo if you'd rather keep the old behaviour.

Nothing is blocked or left open.

**How it works:** `main.ts` hands the arguments to `run` in `src/cli.ts`, which picks the command. For `tag` and `list --tag`, the CLI cleans up the tag with `normalizeTag` (trim, lowercase, allow only `a-z`, `0-9` and `-`). It then calls `BookmarkStore::tag` or `BookmarkStore::listByTag`. `tag` adds the tag once, keeps the order tags were added in, and saves the file. `run` turns `InvalidTagError` into exit 2 and `BookmarkNotFoundError` into exit 1, so the store never prints anything and the CLI never touches the file.