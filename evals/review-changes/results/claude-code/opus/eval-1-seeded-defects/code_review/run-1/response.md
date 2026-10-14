I reviewed `main...HEAD` on `feature/bookmark-tags` (3 commits, no uncommitted changes) and ran the CLI against a temp store file. That reproduced the first four findings below, and I fixed those. Tests now pass (15/15) and the reproduction steps behave correctly. The fixes are **not committed**: your CLAUDE.md says to commit through the `/commit` skill, and that skill isn't available in this session.

```json
[
  {
    "file": "src/store.ts",
    "line": 50,
    "summary": "BookmarkStore.tag adds the tag again even when the bookmark already has it; the plan says a repeated tag should change nothing.",
    "failure_scenario": "`bm tag 1 work` run twice (or `work` then `Work`) saves `\"tags\": [\"work\", \"work\"]` to the store file (reproduced)."
  },
  {
    "file": "src/cli.ts",
    "line": 53,
    "summary": "`list --tag` passes the raw tag to the store without normalizing it, so a mixed-case or padded tag matches nothing and an invalid tag is not rejected.",
    "failure_scenario": "After `bm tag 1 work`, `bm list --tag Work` prints nothing and exits 0 (reproduced); `bm list --tag 'to do'` exits 0 instead of 2 with `invalid tag`."
  },
  {
    "file": "src/cli.ts",
    "line": 21,
    "summary": "BookmarkNotFoundError exits with code 2, but AGENTS.md and the plan say not-found is exit 1.",
    "failure_scenario": "`bm tag 9 work` prints `no bookmark 9` and exits 2 (reproduced), so scripts can't tell 'not found' from 'bad input'. AGENTS.md: \"the CLI maps them to messages and exit codes (1 for not found, 2 for bad input)\"."
  },
  {
    "file": "src/cli.ts",
    "line": 53,
    "summary": "`list --tag` with no value quietly lists every bookmark instead of reporting a usage error.",
    "failure_scenario": "`bm list --tag` prints the whole list and exits 0 (reproduced), so the user wrongly thinks the filter was applied."
  },
  {
    "file": "src/store.ts",
    "line": 55,
    "summary": "The store method is named `listTagged`, but the plan's interface and call chain call it `listByTag`.",
    "failure_scenario": "The code no longer matches the plan, which names `BookmarkStore::listByTag(tag)` in Units, Call chains and Tasks."
  },
  {
    "file": "docs/plans/2026-10-14-bookmark-tags.md",
    "line": 100,
    "summary": "Tasks are ticked as done, but the tests they promise for a duplicate tag and an unknown id (store and CLI) were never written.",
    "failure_scenario": "Nothing catches the first and third findings above; the existing tests passed while both bugs were present."
  },
  {
    "file": "src/cli.ts",
    "line": 42,
    "summary": "`Number(rawId)` accepts ids that aren't plain numbers, such as an empty string, hex or exponent forms.",
    "failure_scenario": "`bm tag '' work` becomes id 0 and prints `no bookmark 0` instead of the usage message; `bm tag 0x1 work` tags bookmark 1."
  },
  {
    "file": "src/cli.ts",
    "line": 47,
    "summary": "The tag is normalized twice: once in the CLI and again in `BookmarkStore.tag`.",
    "failure_scenario": "Repeated work, and it's unclear which layer owns normalization, even though the plan says tags are normalized once."
  }
]
```

**Fixed:**
- **Duplicate tags:** `BookmarkStore.tag` now does nothing if the bookmark already has the normalized tag.
- **Unnormalized filter:** `listTagged` is renamed to `listByTag` and normalizes its argument, so case and whitespace don't matter and invalid tags give `invalid tag` with exit 2.
- **Exit code:** BookmarkNotFoundError now exits 1.
- **Missing `--tag` value:** `list --tag` with no value prints `usage: bm list [--tag <tag>]` and exits 2.
- **Missing tests:** added tests for a repeated tag, an unknown id (store and CLI), normalization in `list --tag`, and `--tag` with no value.

**Skipped:**
- **Loose id parsing:** I left it alone because tightening it changes which ids are accepted, and that wasn't specified.
- **Double normalization:** I kept it on purpose. The store has to own normalization for its direct callers, and the CLI needs the normalized value to print `tagged <id> <tag>`. `normalizeTag` gives the same result when run twice, so the cost is negligible.

Files changed:
- <fixture>`
- <fixture>`
- <fixture>`
- <fixture>`