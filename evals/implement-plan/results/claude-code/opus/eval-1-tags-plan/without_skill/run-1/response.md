Bookmark tags are implemented as the plan describes. All 24 tests pass (there were 4 before), and I tried every command on a temporary store file and got the expected output and exit codes.

**Commits** (one per task, plus one ticking off the tasks in the plan):
1. `tags: add normalizeTag and InvalidTagError` - adds `src/tags.ts` with unit tests for capital letters, surrounding spaces, empty input and invalid characters.
2. `store: add tags to bookmarks` - new bookmarks start with no tags, and store files written before this change load with an empty tag list. A test covers loading such an old file.
3. `store: tag bookmarks and list them by tag` - adds `BookmarkNotFoundError`, `tag()` and `listByTag()`. Adding a tag a bookmark already has does nothing, and tags keep the order they were added in.
4. `cli: add tag command and list --tag` - adds the `tag` command and the `--tag` option on `list`. Errors print `invalid tag: <raw>` (exit 2), `no bookmark <id>` (exit 1), or the usage line (exit 2).
5. `docs: mark bookmark tags plan tasks done`

**Choices the plan didn't cover:**
- `bm list --tag` with no tag, or with extra arguments, prints `usage: bm list [--tag <tag>]` and exits 2.
- `bm tag` exits with the usage message (code 2) if the tag is missing or there are extra arguments, so `bm tag 1 read later` is rejected instead of quietly using only `read`.
- An id counts as numeric only if it is all digits.
- The store expects tags that are already cleaned up, as the plan says ("normalized once"). Only the CLI calls `normalizeTag`.

The `/commit` skill isn't available in this session, so I followed its rules from `~/.claude/skills/commit/SKILL.md` by hand.