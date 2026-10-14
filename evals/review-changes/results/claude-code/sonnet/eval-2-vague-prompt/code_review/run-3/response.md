I found six deviations from the plan in `docs/plans/2026-10-14-bookmark-tags.md` and fixed all of them in the working tree. `npm test` passes with 13 tests.

```json
[
  {"file":"src/store.ts","line":48,"summary":"tag() pushes without a duplicate check, so tagging twice stores the tag twice.","failure_scenario":"`bm tag 1 work` run twice gives tags ['work','work']. The plan says tagging with an existing tag is a no-op."},
  {"file":"src/cli.ts","line":18,"summary":"An unknown id returns exit 2, but the plan says exit 1.","failure_scenario":"`bm tag 99 x` exits 2, so scripts cannot tell a missing bookmark from bad input."},
  {"file":"src/cli.ts","line":53,"summary":"`list --tag` passes the raw tag to the store with no normalization, so it is case-sensitive and unvalidated.","failure_scenario":"After tagging 'work', `bm list --tag Work` prints nothing. An invalid tag does not produce the `invalid tag` error."},
  {"file":"src/store.ts","line":57,"summary":"The method is named listTagged, but the plan specifies listByTag.","failure_scenario":"Code written against the plan's `BookmarkStore::listByTag` API fails to compile."},
  {"file":"src/cli.ts","line":53,"summary":"`bm list --tag` with no value silently lists every bookmark.","failure_scenario":"A user who forgets the tag name gets the full unfiltered list with exit 0 and no hint."},
  {"file":"test/store.tags.test.ts","line":1,"summary":"The plan requires tests for a duplicate tag and an unknown id, and for the unknown-id CLI case. None existed.","failure_scenario":"The duplicate-tag and exit-code bugs above went unnoticed, even though the plan's task checklist is marked done."}
]
```

**Fixed**
- `tag()` now skips a tag the bookmark already has.
- An unknown id now exits 1 in the CLI.
- `listTagged` is renamed to `listByTag`, and it normalizes and validates its input, so `Work` matches 'work' and a bad tag raises `InvalidTagError`.
- `bm list --tag` with no value now prints `usage: bm list [--tag <tag>]` and exits 2.
- Added tests for the duplicate tag, the unknown id in the store, and the unknown-id CLI exit code.

**Skipped**
- I did not run the last plan task, the manual `npm run bm -- add`, `tag` and `list --tag` check against a temp store file. Its checkbox is already marked done in the diff.

The edits are in `src/store.ts`, `src/cli.ts`, `test/store.tags.test.ts` and `test/cli.tags.test.ts`.