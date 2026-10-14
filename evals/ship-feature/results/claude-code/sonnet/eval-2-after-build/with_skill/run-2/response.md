The flow is at the push stop. The tags feature is built and reviewed, and no merge request exists yet.

**Title**
```
bm: tag bookmarks and filter the list by tag
```

**Description**
```
Bookmarks could not be grouped. `bm tag <id> <tag>` now adds a tag to a bookmark, and `bm list --tag <tag>` lists the bookmarks that have it.

- Tags are lowercased and trimmed in one place, `normalizeTag`, so the store and the CLI agree on what a valid tag is. Anything outside `a-z`, `0-9` and `-` is rejected (exit 2).
- Tags are stored on each bookmark in the existing store file. Files written before this change have no `tags` field and are read as `tags: []`, so no migration is needed.
- Tagging a bookmark with a tag it already has is a no-op, not an error.

Review:
1. `bm tag` from `src/cli.ts` `run()` to `BookmarkStore::tag` and `listByTag` in `src/store.ts`: normalization and dedupe live in the store, and the CLI also normalizes for its output line. Check the exit codes (1 for an unknown id, 2 for bad input).
2. `load()` in `src/store.ts`: old files without `tags` are read as `[]`. A corrupt file still throws, as before, so it is never overwritten.
Skim: `src/tags.ts`, the tests, the plan and its review section.
```

An isolated review of the branch found and fixed five problems before this point. These were the wrong exit code for an unknown id, duplicate tags, an unnormalized `list --tag`, a wrong method name and missing tests. I also ran `add`, `tag` and `list --tag` against a temp store file, and the output matched the plan. All 15 tests pass.

The only independent re-check of the review fixes was the reviewer re-reading them, because it could not start a second agent. The `src/store.ts` and `src/cli.ts` changes are the ones to read closely.

Commits by step:
- **Design:** `b1998c5`
- **Build:** `550c919`, `82bc0cc`, `00b29b2`
- **Review:** `0340fd5`, `d39cc05`

Do you want me to push `feature/bookmark-tags` and open the merge request against `main`?