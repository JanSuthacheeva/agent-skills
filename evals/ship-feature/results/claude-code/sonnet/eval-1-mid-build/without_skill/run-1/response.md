The bookmark tags feature is finished: `bm tag <id> <tag>` and `bm list --tag <tag>` both work. All 17 tests pass. There is no lint or type-check script in the project, so I only ran the tests. Nothing was pushed.

**Tasks and commits**
- `a17a8da` - `tags` on `Bookmark`, new bookmarks start with `tags: []`, and files written before tags existed load as `[]`.
- `131c283` - `BookmarkNotFoundError`, `BookmarkStore::tag` and `listByTag`, tested for a duplicate tag and an unknown id.
- `1f0ebc7` - the `tag` command and `list --tag` in `run`, with CLI tests for both, an invalid tag and an unknown id.
- `d41c0a6` - ticks the final task in the plan.

**End-to-end check**
- **Commands:** I ran the real CLI against a temp store file.
- **Tagging:** `tag 2 " Work "` printed `tagged 2 work`, and tagging again was a silent no-op.
- **Filtering:** `list --tag work` printed only bookmark 2.
- **Errors:** an invalid tag exited 2 with `invalid tag: to do`, an unknown id exited 1 with `no bookmark 9`, and a non-numeric id exited 2 with the usage line.
- **Store file:** it holds the `tags` field.

**Deviation from the plan**
- `list` with a missing `--tag` value or an unknown option now prints `usage: bm list [--tag <tag>]` and exits 2. The plan didn't cover that case. I added the line to the plan's Errors section.

**Nothing is blocked or left open.**

**How it works**
- **Entry point:** `main` calls `run(argv, store, out)` in `src/cli.ts`.
- **Normalizing:** `run` calls `normalizeTag` from `src/tags.ts`, so the store only ever sees valid tags.
- **Storing:** `BookmarkStore.tag` and `listByTag` do the work, and `load` fills in `tags: []` for old files.
- **Errors:** a small helper in `cli.ts`, `withTagErrors`, turns `InvalidTagError` into exit 2 and `BookmarkNotFoundError` into exit 1.