Bookmark tags are built: `bm tag <id> <tag>` and `bm list --tag <tag>` work, and all 5 plan tasks are done and ticked. All 25 tests pass. Before I started, the existing 4 tests already passed. The project has no lint or type-check setup, so I only ran the tests.

**Commits**
1. `9c8768a` - `normalizeTag` and `InvalidTagError` in `src/tags.ts`
2. `d04a2cf` - `Bookmark.tags`; new bookmarks get `tags: []`; files saved before this change load as untagged
3. `f41e5ff` - `BookmarkNotFoundError`, `BookmarkStore::tag` and `BookmarkStore::listByTag`
4. `0faaeae` - the `tag` command and the `list --tag` option
5. `edf3d27` - final plan tick, after the end-to-end run

**End-to-end check:** I ran `npm run bm` against a temp file that started in the old format, with no `tags` field.
- `tag 2 " Runtime "` printed `tagged 2 runtime`.
- `list --tag RUNTIME` listed the two tagged bookmarks in the same format as `list`, including the one from the old file.
- Tagging a bookmark with a tag it already has changed nothing.
- `tag 9 work` printed `no bookmark 9` and exited with 1.
- `tag 2 "to read"` printed `invalid tag: to read` and exited with 2.
- `tag x work` printed the usage message and exited with 2.
- The saved file kept the same format, now with a `tags` array on each bookmark.

**Differences from the plan** (I've updated the plan to match):
- `run` now hands off to a private `dispatch` function, so the two error types are turned into messages and exit codes in one place. Nothing visible changes.
- The plan didn't say what happens on bad `list` input. `list` with an unknown option, or `--tag` with no value, now prints `usage: bm list [--tag <tag>]` and exits with 2. `tag` with no tag argument prints the same usage message as a non-numeric id. These are new messages users will see, so tell me if you want different wording.
- Your instructions say to commit with the `/commit` skill, but it isn't installed here. I committed with plain git, using the existing `bm:` / `docs:` message style.

Nothing is blocked or left open. Nothing is pushed.

**How it works:** `main` passes the arguments to `run`. For `tag`, it checks that the id is a number, then `normalizeTag` trims and lowercases the tag and only allows `a-z`, `0-9` and `-`. `BookmarkStore::tag` loads the file, adds the tag unless the bookmark already has it, and saves. For `list --tag`, the tag is normalized the same way and `BookmarkStore::listByTag` returns the matching bookmarks. Older files work without a migration because `load()` treats a missing `tags` field as empty.