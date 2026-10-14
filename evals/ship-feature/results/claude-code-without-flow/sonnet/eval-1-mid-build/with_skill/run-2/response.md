The build and the review are done, and no merge request exists yet for `feature/bookmark-tags`. The flow is now at the push stop.

**Where it stands**
- All five plan tasks are ticked and committed.
- The review found one bug: `bm tag "" work` read the empty id as 0 and reported `no bookmark 0`. It is fixed in `c83a5fa` with a test.
- The `## Review` section has no open items.
- The suite is green at 20 of 20. The repo has no linter or type checker.

**Title**
```
bm: tag bookmarks and filter the list by tag
```

**Description**
```
Bookmarks could not be grouped or found by topic. Each bookmark now carries tags, `bm tag <id> <tag>` adds one, and `bm list --tag <tag>` shows only the bookmarks with that tag.

- Tags are stored on each bookmark in the existing store file, so the file format stays a JSON array and no migration is needed. Files written before this change load with `tags: []` and only get the field on disk at the next write.
- `normalizeTag` is the single definition of a valid tag: lowercased, trimmed, only `a-z`, `0-9` and `-`. The store normalizes again, so it stays safe when called without the CLI.
- Tagging a bookmark with a tag it already has is a no-op, not an error.
- `list --tag` with no value prints `usage: bm list [--tag <tag>]` and exits 2. The plan did not cover this case.

Review:
1. `src/store.ts` `load()` to `save()`: old files without `tags` load as `[]`. Check that a corrupt file still throws and is never overwritten.
2. `bm tag` from `src/cli.ts` `run()` and `dispatch()` to `BookmarkStore::tag`: check the error mapping (invalid tag gives 2, unknown id gives 1, bad id gives usage and 2).
Skim: `src/tags.ts`, `src/bookmark.ts` and the tests.
```

The fix in `c83a5fa` changed production code and was re-read by the reviewer, not by an independent agent. The commits and the description use no ticket ID, so there is no `Refs:` line.

Should I push `feature/bookmark-tags` and open the merge request against `main`?