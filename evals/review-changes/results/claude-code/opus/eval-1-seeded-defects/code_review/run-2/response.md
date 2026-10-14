```json
[
  {"file": "src/store.ts", "line": 50, "summary": "BookmarkStore.tag pushes the tag even when the bookmark already has it, but the plan says a repeated tag should do nothing.", "failure_scenario": "`bm tag 1 work` twice -> tags becomes [\"work\",\"work\"], which breaks the 'without duplicates' rule in the plan"},
  {"file": "src/cli.ts", "line": 21, "summary": "BookmarkNotFoundError is mapped to exit code 2, but AGENTS.md and the plan say not found is exit 1.", "failure_scenario": "`bm tag 99 work` exits 2, so scripts can't tell 'not found' apart from bad input. Breaks the AGENTS.md rule \"exit codes (1 for not found, 2 for bad input)\""},
  {"file": "src/cli.ts", "line": 53, "summary": "`list --tag` sends the raw tag to the filter without normalizing it, so mixed-case or padded input matches nothing and invalid tags are not rejected.", "failure_scenario": "`bm tag 1 Work` stores `work`, then `bm list --tag Work` prints nothing. `bm list --tag 'to do'` exits 0 when it should print `invalid tag` and exit 2"},
  {"file": "src/cli.ts", "line": 53, "summary": "`list --tag` with no value, or any unknown option, quietly lists every bookmark instead of reporting bad input.", "failure_scenario": "`bm list --tag` (value forgotten) or `bm list --tga work` prints all bookmarks with exit 0, so the user thinks the filter worked"},
  {"file": "src/cli.ts", "line": 42, "summary": "The id is parsed with `Number()`, which accepts empty, whitespace, hex and decimal strings.", "failure_scenario": "`bm tag \"\" work` -> Number('') is 0 -> prints 'no bookmark 0' instead of the usage message. `bm tag 0x1 work` or `bm tag 1.0 work` tags bookmark 1"},
  {"file": "src/store.ts", "line": 55, "summary": "The method is named `listTagged`, but the plan's interface specifies `listByTag`.", "failure_scenario": "The code and the plan disagree, so anyone following the documented interface calls a method that doesn't exist"},
  {"file": "docs/plans/2026-10-14-bookmark-tags.md", "line": 100, "summary": "Plan tasks are ticked as done, but the promised tests for a duplicate tag and an unknown id (store and CLI) were never written.", "failure_scenario": "The duplicate-tag bug and the wrong exit code above went out with no test catching them, while the plan claims they are covered"}
]
```

I applied all 7 findings and left them uncommitted for you to review. 17 tests pass, up from 10. I also ran the real CLI against a temp store file: tagging twice stores one tag, `list --tag WORK` finds the bookmark, and an unknown id exits 1.

**Fixed:**
- **Repeated tags:** `src/store.ts` `tag()` now normalizes the tag first and does nothing if the bookmark already has it.
- **Lookup by tag:** `listTagged` is renamed to `listByTag` to match the plan, and it now normalizes the tag. So invalid tags raise `InvalidTagError` (exit 2) and `--tag Work` matches `work`.
- **Exit code:** in `src/cli.ts`, an unknown id now exits 1.
- **Id parsing:** `tag` only accepts ids matching `/^\d+$/`; anything else gets the usage message.
- **`list` options:** `--tag` with no value, or any other option, now prints `usage: bm list [--tag <tag>]` and exits 2.
- **Missing tests:** added store tests for a repeated tag and an unknown id, and CLI tests for an unknown id, a non-numeric id, a mixed-case `--tag`, an invalid `--tag` and `--tag` with no value.

**Skipped:**
- The tag is still normalized twice, once in the CLI and once in the store. That costs nothing, and it keeps the store safe for callers that don't go through the CLI.
- I didn't commit. Your CLAUDE.md says to use the `/commit` skill, and it isn't available in this session.

Changed files:
- <fixture>
- <fixture>
- <fixture>
- <fixture>