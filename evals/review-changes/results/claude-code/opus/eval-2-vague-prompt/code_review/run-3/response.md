I reviewed `main...HEAD` on `feature/bookmark-tags` and found 8 issues. I reproduced the main bugs by running the CLI against a temp store file, then fixed all of them. The tests now pass (18 of 18, up from 10), and the CLI behaves correctly when rerun by hand.

```json
[
  {"file": "src/store.ts", "line": 50, "summary": "`BookmarkStore.tag` adds a tag even when the bookmark already has it, but the plan says that should be a no-op.", "failure_scenario": "`bm tag 1 work` then `bm tag 1 Work` saves `\"tags\": [\"work\", \"work\"]` (reproduced)."},
  {"file": "src/cli.ts", "line": 52, "summary": "`list --tag` sends the raw tag to the store without cleaning it up or checking it, so the search only works if the user types it exactly in lowercase.", "failure_scenario": "After tagging bookmark 1 `work`, `bm list --tag Work` prints nothing and exits 0. `bm list --tag 'to do'` exits 0 instead of printing `invalid tag` with exit 2."},
  {"file": "src/cli.ts", "line": 21, "summary": "An unknown bookmark id exits with code 2, but AGENTS.md and the plan say not-found is exit 1.", "failure_scenario": "`bm tag 9 work` prints `no bookmark 9` and exits 2, so scripts can't tell a missing bookmark from bad input."},
  {"file": "src/cli.ts", "line": 52, "summary": "`list --tag` with no tag after it, or any unknown option, quietly lists every bookmark.", "failure_scenario": "`bm list --tag` exits 0 and prints the whole list, so the user thinks they filtered when they didn't."},
  {"file": "src/cli.ts", "line": 42, "summary": "Converting the id with `Number(rawId)` treats an empty or whitespace-only id as 0.", "failure_scenario": "`bm tag \"\" work` prints `no bookmark 0` instead of the usage message. Hex input like `0x1` is also accepted."},
  {"file": "src/store.ts", "line": 55, "summary": "The method is named `listTagged`, but the plan's interface calls it `listByTag`.", "failure_scenario": "The plan's call chain refers to `BookmarkStore::listByTag`, which doesn't exist, so anyone following the plan hits a missing method."},
  {"file": "test/store.tags.test.ts", "line": 19, "summary": "The plan's task list is all checked off, but the promised tests for a duplicate tag and an unknown id are missing.", "failure_scenario": "The duplicate-tag bug got through because nothing tested it."},
  {"file": "test/cli.tags.test.ts", "line": 26, "summary": "The CLI tests the plan promised for an unknown id and for `list --tag` input handling are missing.", "failure_scenario": "The wrong exit code and the case-sensitive `list --tag` bug weren't caught by any test."}
]
```

**What I fixed:**
- <fixture>`:**
  - Tagging a bookmark with a tag it already has no longer changes or saves anything.
  - `listTagged` is renamed to `listByTag` and now lowercases and trims the tag first.
- <fixture>`:**
  - Not-found now exits with code 1.
  - The id must be all digits (`/^\d+$/`), otherwise the usage message is shown.
  - `list` with `--tag` but no tag, or with an unknown option, prints `usage: bm list [--tag <tag>]` and exits 2.
  - `list --tag` goes through `listByTag`, so an invalid tag now gives `invalid tag` with exit 2.
- <fixture>` and <fixture>`:** added 8 tests covering:
  - a duplicate tag
  - an unknown id, both in the store and in the CLI
  - an empty or non-numeric id
  - `list --tag` lowercasing the tag, rejecting an invalid tag, and rejecting a missing tag

**Skipped:**
- The `tag` command still cleans up the tag both in the CLI and again in the store. The CLI needs the cleaned tag for its output line, and the store keeps it for safety.
- The changes are not committed. Your CLAUDE.md says to use the `/commit` skill, but it isn't available in this session.