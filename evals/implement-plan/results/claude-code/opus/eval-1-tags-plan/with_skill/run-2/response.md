I've built bookmark tags as the plan describes: `bm tag <id> <tag>` and `bm list --tag <tag>` both work. All 23 tests pass (4 before, 19 new). The project has no lint or type-check scripts, so only tests were run.

**Commits, one per task:**
- `e6346a4` - `normalizeTag` and `InvalidTagError`
- `bb173b4` - bookmarks now have a `tags` field, and older store files load with `tags: []`
- `c7a1196` - `BookmarkNotFoundError`, `BookmarkStore::tag`, `BookmarkStore::listByTag`
- `f3b9f21` - the `tag` command and the `--tag` option on `list`
- `b2e11b2` - ticks the last task, the end-to-end check, in the plan

**End-to-end check:** I ran the real CLI against a temp store file that started with one bookmark written before tags existed:
- `" Work "` was saved as `work`, and tagging a bookmark twice with the same tag added it only once.
- `list --tag WORK` printed only the two bookmarks tagged `work`, including the old one.
- The error cases gave the planned messages and exit codes: an invalid tag exits 2, an unknown id exits 1, a non-numeric id prints the usage line and exits 2.
- The old bookmark was saved back with its `tags` field.

**Where I changed the plan (it's updated to match):**
- `InvalidTagError` keeps the original input in a `raw` field and `BookmarkNotFoundError` keeps the `id`. That way the CLI writes its own error messages, which is how AGENTS.md says errors should work.
- The plan didn't say what `list --tag` should do with no tag after it. It now prints `usage: bm list [--tag <tag>]` and exits 2, like the other bad-input cases. That message is something users will see, so change it if you want different wording.
- Your instructions say to commit with the `/commit` skill, but it isn't installed here. I used plain `git commit` with the repo's `bm: ...` message style.

**How it works:** `main.ts` calls `run(argv, store, out)` in `src/cli.ts`.
- `run` hands the arguments to a private `dispatch` function, then turns `InvalidTagError` into exit 2 and `BookmarkNotFoundError` into exit 1.
- For `tag`, `dispatch` checks the arguments and cleans up the tag with `normalizeTag` (`src/tags.ts`: trim, lowercase, only `a-z`, `0-9` and `-` allowed). It then calls `store.tag(id, tag)`, which loads the file, finds the bookmark, adds the tag if it's new, and saves.
- For `list --tag`, `dispatch` cleans up the tag the same way, calls `store.listByTag`, and prints the results in the same format as `list`.
- Old store files need no migration: `BookmarkStore::load` gives any bookmark without tags an empty list.

Nothing is blocked. I haven't pushed anything.