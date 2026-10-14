No merge request exists for the branch yet, and the repo has no template. Here is the draft.

**Title**

`bm: tag bookmarks and filter the list by tag`

**Description**

```
Bookmarks could not be grouped or found by topic. `bm tag <id> <tag>` now
adds a tag to a bookmark and `bm list --tag <tag>` lists only the
bookmarks with that tag.

- Tags are normalized in one place, `normalizeTag` (trimmed, lowercased,
  only `a-z`, `0-9` and `-`), so the store and the CLI agree on what a
  valid tag is.
- Tags are stored on each bookmark in the existing store file, with no
  migration. Files written before this change have no `tags` field and
  `load()` reads them as `[]`.
- Tagging a bookmark with a tag it already has is a no-op, not an error.

Review:
1. `BookmarkStore::load` and `tag` in `src/store.ts`: old files without
   `tags` still load, and nothing is written back until the next save.
2. `bm tag` and `bm list --tag` from `src/cli.ts` `run()`: invalid tag
   exits 2, unknown id exits 1, non-numeric id prints usage and exits 2.
Skim: `src/tags.ts` and the tests.

Left open: `bm list --tag` without a value lists every bookmark. The plan
does not cover it.
```

Notes:
- The tree is clean, so there are no uncommitted changes to mention.
- No ticket ID in the branch name, so there is no `Refs:` line.
- Nothing needs deploying. There are no new dependencies, environment variables or migrations.
- The review's fixes were not independently reviewed, because no fresh agent was available for that.

Push `feature/bookmark-tags` and open the merge request against `main`?