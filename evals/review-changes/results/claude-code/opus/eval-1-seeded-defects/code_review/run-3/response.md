I found 8 defects on `feature/bookmark-tags` compared with `main`, and fixed all 8 in the working tree. I reproduced the main ones by running the real CLI against a temp store, then confirmed the fixes the same way. Tests went from 10 to 16 and all pass. Nothing is committed yet: your CLAUDE.md says to commit with the `/commit` skill, which isn't available to me.

```json
[
  {"file": "src/cli.ts", "line": 21, "summary": "BookmarkNotFoundError maps to exit 2, but AGENTS.md and the plan say not-found exits 1.", "failure_scenario": "`bm tag 9 work` on a store without id 9 prints 'no bookmark 9' and exits 2 (reproduced), so scripts can't tell 'not found' from 'bad input'."},
  {"file": "src/store.ts", "line": 50, "summary": "tag() always pushes the tag, so repeating a tag stores a duplicate; the plan says it should be a no-op.", "failure_scenario": "`bm tag 1 work` twice leaves tags [\"work\",\"work\"] in the store file (reproduced)."},
  {"file": "src/cli.ts", "line": 53, "summary": "`list --tag` passes the raw argument to listTagged without normalizing it (the plan's call chain does normalize).", "failure_scenario": "After `bm tag 1 work`, `bm list --tag Work` prints nothing (reproduced), and `list --tag 'to do'` prints an empty result instead of 'invalid tag'."},
  {"file": "src/cli.ts", "line": 53, "summary": "`list --tag` with no value, or any unknown list argument, quietly falls back to listing everything.", "failure_scenario": "`bm list --tag` exits 0 and prints every bookmark (reproduced), when it should give a usage error."},
  {"file": "src/cli.ts", "line": 42, "summary": "The `Number(rawId)` + `Number.isInteger` check accepts non-numeric ids like '', ' ' and '1e0'.", "failure_scenario": "`bm tag '' work` treats the id as 0 and reports 'no bookmark 0' instead of the usage error the plan specifies."},
  {"file": "src/store.ts", "line": 56, "summary": "The method is named listTagged, but the plan specifies listByTag.", "failure_scenario": "The code no longer matches the documented interface in docs/plans/2026-10-14-bookmark-tags.md."},
  {"file": "docs/plans/2026-10-14-bookmark-tags.md", "line": 100, "summary": "Tasks are checked off, but the tests they promise (duplicate tag, unknown id at store and CLI level) don't exist.", "failure_scenario": "The plan claims the work is done, and the duplicate-tag and exit-code bugs above went undetected."},
  {"file": "test/store.tags.test.ts", "line": 19, "summary": "Nothing tests listing by a tag in a different case or with surrounding whitespace.", "failure_scenario": "The `list --tag Work` mismatch passes the test suite."}
]
```

**What changed:**
- **`src/cli.ts`:**
  - Not-found now exits 1.
  - `tag` requires a numeric id (digits only) and exactly two arguments.
  - `list` accepts either no arguments or exactly `--tag <tag>`. Anything else prints `usage: bm list [--tag <tag>]` and exits 2.
- **`src/store.ts`:**
  - `tag()` doesn't add a tag the bookmark already has.
  - `listTagged` is renamed to `listByTag` and normalizes its input, so an invalid tag now gets the 'invalid tag' error.
- **`test/store.tags.test.ts`:** new tests for the duplicate no-op, an unknown id, and case-insensitive `listByTag`.
- **`test/cli.tags.test.ts`:** new tests for `list --tag Work`, exit 1 on an unknown id, an empty id, and `list --tag` with no value.

Nothing was skipped.

Files are in <fixture>`:
- `src/cli.ts`
- `src/store.ts`
- `test/store.tags.test.ts`
- `test/cli.tags.test.ts`