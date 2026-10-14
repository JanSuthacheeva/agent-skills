Bookmark tags are in: `bm tag <id> <tag>` and `bm list --tag <tag>` work as the plan describes. All 21 tests pass (up from 4), and I committed each task as I finished it (5 commits).

**One fix to the plan.** As written, the plan's `InvalidTagError` would have crashed on load. `constructor(readonly raw: string)` is a parameter property: Node 22 refuses to run it, and AGENTS.md forbids them. I tried it with a small file and Node rejected it. I changed it to an ordinary `readonly raw: string` field set in the constructor. Callers still read `err.raw` the same way, and I updated the plan file to match.

**What's in each file:**
- `src/tags.ts`: `normalizeTag` trims and lowercases, then allows only `a-z`, `0-9` and `-`. Anything else, including empty input, throws `InvalidTagError` with the original input.
- `src/store.ts`: new bookmarks start with no tags, and older store files without a `tags` field load as untagged. `tag()` keeps tags in the order they were added, and adding a tag a bookmark already has does nothing. An unknown id throws `BookmarkNotFoundError`.
- `src/cli.ts`: invalid tag prints `invalid tag: <raw>` (exit 2), unknown id prints `no bookmark <id>` (exit 1), and a non-numeric or missing id prints the usage line (exit 2).

**Two choices the plan didn't cover:**
- `bm list --tag` with no value, or any other option on `list`, prints `usage: bm list [--tag <tag>]` and exits 2.
- Extra arguments after `bm tag <id> <tag>` are also treated as bad usage.

**Checked by hand:** I ran the real CLI with `npm run bm` against a temp store file written in the old format, without tags. Adding, tagging (including mixed case, padding and duplicates), and listing by tag all printed what the plan specifies. The error cases gave the right messages and exit codes, and the saved file has the `tags` field.

**Not done:**
- The `/commit` skill isn't installed here, so I committed with plain git in the repo's existing message style.
- There's no TypeScript compiler in the project, so types were never checked separately. Node only strips them when running, so a type mistake wouldn't show up in the tests.