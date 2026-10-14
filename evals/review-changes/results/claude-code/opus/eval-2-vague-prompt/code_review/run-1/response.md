I reviewed `main...HEAD` (4 commits on `feature/bookmark-tags`), confirmed every bug below by running the real CLI (`npm run bm` against a temp `BM_FILE`), and fixed them all. Tests now pass (16, up from 10), and re-running the CLI gives the expected output for each case.

```json
[
  {
    "file": "src/store.ts",
    "line": 50,
    "summary": "BookmarkStore.tag always pushes the tag, so tagging a bookmark with a tag it already has adds a duplicate, while the plan says it should do nothing.",
    "failure_scenario": "`bm tag 1 work` then `bm tag 1 Work` -> the store file holds tags [\"work\",\"work\"], breaking the 'no duplicates' rule in the plan."
  },
  {
    "file": "src/cli.ts",
    "line": 53,
    "summary": "`list --tag` passes the raw tag to the store without normalizing it, so filtering is case/whitespace sensitive and invalid tags are not rejected.",
    "failure_scenario": "Bookmark tagged `work`; `bm list --tag Work` prints nothing with exit 0. `bm list --tag 'to do'` prints nothing instead of `invalid tag`, exit 2."
  },
  {
    "file": "src/cli.ts",
    "line": 21,
    "summary": "An unknown id exits 2, but the plan says 1.",
    "failure_scenario": "`bm tag 9 work` prints `no bookmark 9` and exits 2, so a script can't tell 'not found' apart from bad usage."
  },
  {
    "file": "src/cli.ts",
    "line": 53,
    "summary": "`list --tag` with no value, or any unknown flag, silently lists every bookmark instead of showing a usage error.",
    "failure_scenario": "`bm list --tag` (value forgotten) prints all bookmarks with exit 0, so it looks like the filter matched everything."
  },
  {
    "file": "src/cli.ts",
    "line": 42,
    "summary": "`Number(rawId)` with `Number.isInteger` accepts '', '1e0', '0x1', ' 1 ' and negative numbers as ids.",
    "failure_scenario": "`bm tag \"\" work` reports `no bookmark 0` (exit 2) instead of the usage error the plan specifies for a non-numeric id."
  },
  {
    "file": "test/store.tags.test.ts",
    "line": 19,
    "summary": "The plan's tasks are ticked as done with tests for a duplicate tag and an unknown id, but those tests (store and CLI) don't exist, which is why the bugs above weren't caught.",
    "failure_scenario": "The duplicate-tag bug and the wrong exit code pass the whole test suite."
  },
  {
    "file": "src/store.ts",
    "line": 55,
    "summary": "The store method is named `listTagged`, but the plan's interface names it `listByTag`.",
    "failure_scenario": "The code and the plan disagree, so anyone following the plan or its call chains calls a method that doesn't exist."
  }
]
```

**Fixed:**
- <fixture>`**
  - `tag` now does nothing if the bookmark already has the tag.
  - `listTagged` is renamed to `listByTag` and normalizes its input.
- <fixture>`**
  - An unknown id now exits 1.
  - The id must match `^\d+$`.
  - `list` now rejects a missing `--tag` value or extra arguments with `usage: bm list [--tag <tag>]`, exit 2.
- **Tests:**
  - `test/store.tags.test.ts` gains a duplicate-tag test and an unknown-id test.
  - `test/cli.tags.test.ts` gains tests for `list --tag` normalization, a missing tag value, unknown id exiting 1, and non-numeric ids.

**Skipped:** nothing. The tag is normalized twice (once in the CLI, once in the store), which is harmless and matches the plan's call chain, so I left it.

**Not committed:** your CLAUDE.md says to commit through the `/commit` skill, but that skill isn't available here, so the changes are uncommitted in the working tree.