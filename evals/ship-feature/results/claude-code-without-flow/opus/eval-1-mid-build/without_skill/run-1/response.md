The bookmark tags feature is finished. All five tasks in `docs/plans/2026-10-14-bookmark-tags.md` are ticked, the 16 tests pass (6 before I started), and I ran the real CLI end to end. The project has no lint or type-check tooling, so neither was run.

**Commits** (task 1, `bfaa882`, was already done):
- `40ebd76 bm: store tags on bookmarks`: every bookmark gets a `tags` list. Store files written before tags existed load as having no tags, so no migration is needed.
- `0c2d284 bm: tag bookmarks and list them by tag`: the store can add a tag to a bookmark and find bookmarks by tag. It rejects unknown ids, and adding a tag twice does nothing.
- `144bcde bm: add tag command and list --tag`: the two new commands, with tests for success, an invalid tag, an unknown id and a non-numeric id.
- `28d1b3f docs: verify bookmark tags end to end`: ticks the last task.

**End-to-end check:** I started with a store file in the old format (no `tags` field), then added two bookmarks and tagged all three. Every case gave the planned output and exit code:
- `bm list` still read the old file.
- `bm tag 1 " Legacy "` printed `tagged 1 legacy`.
- Tagging a bookmark with a tag it already has printed the same line and changed nothing.
- `bm list --tag RUNTIME` printed bookmarks 2 and 3.
- An unknown tag printed nothing and exited 0.
- `bm tag 9 work` printed `no bookmark 9`, exit 1.
- `bm tag x work` printed the usage line, exit 2.
- `bm tag 1 "to do"` printed `invalid tag: to do`, exit 2.

**Where I went beyond the plan** (all recorded in the plan file):
- **`list` usage error:** `list --tag` with no value, or any other option, prints `usage: bm list [--tag <tag>]` and exits 2. The plan didn't cover this; I followed the existing `add` usage style.
- **Missing tag:** `bm tag <id>` with no tag prints the same usage line as a non-numeric id.
- **Error handling in one place:** `run` turns the two error types into messages and exit codes, and the commands live in a private helper it wraps. This matches how AGENTS.md describes CLI errors.
- **Confirmation line:** `tagged <id> <tag>` uses the id as stored, so `bm tag 007 x` prints `tagged 7 x`.

**How it works:** `main.ts` calls `run` in `src/cli.ts`, which picks the command. For `tag` and `list --tag`, it cleans up the tag with `normalizeTag` in `src/tags.ts` (trim, lowercase, only `a-z`, `0-9` and `-` allowed). It then calls `tag` or `listByTag` in `src/store.ts`, which reads and writes the JSON file. Nothing is left open; nothing is pushed and no merge request is opened.