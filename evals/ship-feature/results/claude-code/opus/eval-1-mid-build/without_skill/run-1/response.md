The bookmark tags feature is done: all five plan tasks are complete and committed on `feature/bookmark-tags`. The 16 tests pass, up from 6 before I started. The project has no lint or type check set up, so tests were the only automated check. Nothing is pushed.

**Commits**
- `877e906` bm: store tags on bookmarks (old store files load with `tags: []`, no migration)
- `9a7be8d` bm: store: tag bookmarks and list them by tag (also adds `BookmarkNotFoundError`)
- `dcd13a6` bm: cli: add tag command and list --tag
- `f7f488a` docs: check bookmark tags end to end (ticks the last task in the plan)

**End-to-end check:** I ran `npm run bm` against a temporary store file:
- `bm tag 2 " Work "` printed `tagged 2 work`. Tagging again changed nothing.
- `bm list --tag WORK` listed only the tagged bookmark.
- An unknown id printed `no bookmark 9` and exited with 1.
- An invalid tag (`to do`) and a non-numeric id each printed their error and exited with 2.
- A store file written before tags existed listed, tagged and filtered normally.

**Changes from the plan** (the plan file is updated to match):
- `run` now only turns errors into messages and exit codes. The commands moved into a private `dispatch` function. This is internal only.
- **Needs your OK:** `bm list` now rejects anything other than `--tag <tag>` with `usage: bm list [--tag <tag>]` and exits with 2. The plan didn't say what `list --tag` with no value should do. Before this change, `list` silently ignored extra arguments, so this is a visible behaviour change. It's one line to revert if you'd rather keep ignoring them.
- `tag` with no tag argument gives the same usage error as a non-numeric id.

**Not covered:** `list` still doesn't show tags in its output, which matches the plan.

**How it works:**
1. `main.ts` calls `run(argv, store, out)` in `cli.ts`.
2. The CLI normalizes the raw tag once with `normalizeTag` in `tags.ts`. It trims and lowercases the tag, and rejects it unless it uses only `a-z`, `0-9` and `-`.
3. The CLI then calls `BookmarkStore.tag(id, tag)` or `listByTag(tag)`.
4. The store loads the JSON file and treats a missing `tags` field as `[]`. It adds a tag only if the bookmark doesn't already have it, and saves only when something changed.
5. `run` turns `InvalidTagError` into exit 2 and `BookmarkNotFoundError` into exit 1, so the CLI never reads or writes the file itself.