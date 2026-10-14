```json
[
  {"file": "src/store.ts", "line": 50, "summary": "BookmarkStore.tag pushes the tag even when the bookmark already has it, so duplicates get saved. The plan says re-tagging should do nothing.", "failure_scenario": "`bm tag 1 work` run twice -> the store file holds `\"tags\": [\"work\", \"work\"]`"},
  {"file": "src/cli.ts", "line": 53, "summary": "`list --tag` passes the raw argument to the filter without normalizing it, so filtering is case- and whitespace-sensitive and invalid tags are never reported.", "failure_scenario": "tag 1 with `work`, then `bm list --tag Work` -> prints nothing with exit 0. `bm list --tag 'to do'` -> exit 0 instead of `invalid tag`, exit 2"},
  {"file": "src/cli.ts", "line": 21, "summary": "BookmarkNotFoundError exits with code 2, but AGENTS.md says 'exit codes (1 for not found, 2 for bad input)' and the plan says exit 1.", "failure_scenario": "`bm tag 9 work` with no bookmark 9 -> rc=2, so scripts can't tell 'not found' from 'bad input'"},
  {"file": "src/cli.ts", "line": 53, "summary": "`list` ignores a malformed or unknown option and silently lists every bookmark.", "failure_scenario": "`bm list --tag` (value missing) or `bm list --tags work` -> prints all bookmarks with exit 0 instead of a usage error"},
  {"file": "src/cli.ts", "line": 42, "summary": "`Number(rawId)` with `Number.isInteger` accepts '', ' ', '0x1' and '1e0' as valid ids.", "failure_scenario": "`bm tag '' work` -> `no bookmark 0` instead of the usage error. `bm tag 0x1 work` tags bookmark 1"},
  {"file": "src/store.ts", "line": 55, "summary": "The method is named `listTagged`, but the plan's interface names it `BookmarkStore::listByTag(tag)`.", "failure_scenario": "The code doesn't match the documented design, and anyone following the plan calls a method that doesn't exist"},
  {"file": "test/store.tags.test.ts", "line": 19, "summary": "Plan tasks marked [x] promise tests for a duplicate tag, an unknown id (store and CLI), but none exist.", "failure_scenario": "The duplicate-tag and exit-code bugs above went out with a green test suite"},
  {"file": "docs/plans/2026-10-14-bookmark-tags.md", "line": 102, "summary": "Task 5 (manual run of add, tag and list --tag) is ticked, but running it shows the duplicate-tag and case-sensitivity bugs, so it was not really checked.", "failure_scenario": "The plan claims a verification that would have caught the first two findings"}
]
```

I applied all 8 fixes in the working tree. All 17 tests pass (10 before, 7 new), and I re-ran the commands against a temp store to check the behavior.

- **`src/store.ts`**
  - `tag` now does nothing if the bookmark already has the tag.
  - Renamed `listTagged` to `listByTag`, as in the plan. It now normalizes its argument, so `list --tag Work` finds `work` and an invalid tag gives `invalid tag: <raw>`, exit 2.
- **`src/cli.ts`**
  - "Not found" now exits with 1.
  - The `tag` id must be all digits (`/^\d+$/`), otherwise it prints the usage line.
  - `list` takes either no option or exactly `--tag <tag>`. Anything else prints `usage: bm list [--tag <tag>]` and exits 2.
- **Tests**: added cases to `test/store.tags.test.ts` (duplicate tag, unknown id, case-insensitive filter) and `test/cli.tags.test.ts` (unknown id exits 1, bad ids, `list --tag` normalization, bad `list` options, invalid tag on `list`).
- **Plan doc**: no edit needed. Its ticked tasks are true now that the tests exist and the bugs are fixed.

Skipped: none.

**Not committed.** The changes are in the working tree only. Your CLAUDE.md says to always use the `/commit` skill, and it isn't available in this session, so you'll need to commit them.

Files changed:
- <fixture>
- <fixture>
- <fixture>
- <fixture>