I found 8 issues and fixed all of them; nothing was skipped. The full suite passes (17 tests, 7 of them new), and a manual run of `add` / `tag` / `list --tag` against a temporary store file works. I haven't committed the changes: your instructions require the `/commit` skill, and it isn't available in this session.

The worst one is data loss: if the store file is corrupt, `load()` swallows the parse error and returns an empty list, and the next `bm add` then overwrites the whole file. I reproduced this from the command line before fixing it.

Findings, most severe first:

```json
[
  {"file":"src/store.ts","line":27,"summary":"load() catches JSON parse errors and returns [], so the next write overwrites a corrupt or partly written store file and loses every bookmark.","failure_scenario":"File holds '[{\"id\":1,...},' (truncated) -> `bm add https://x.dev X` prints 'added 1' and replaces the file with a single bookmark. All earlier bookmarks are gone (reproduced)."},
  {"file":"src/cli.ts","line":40,"summary":"The `tag` command reimplements tagging in the CLI (list, find, push, store.save) instead of calling BookmarkStore.tag, which breaks the AGENTS.md rule 'The CLI never touches the file directly' and the plan's call chain.","failure_scenario":"There are two tagging paths that already behave differently (the store warns on duplicates, the CLI does not). BookmarkStore.tag goes unused by the CLI, and future fixes to one path will miss the other."},
  {"file":"src/store.ts","line":66,"summary":"listByTag only normalizes the tag inside the filter callback, so an invalid tag is never checked when the store is empty or the callback never runs.","failure_scenario":"Empty store -> `bm list --tag \"to do\"` exits 0 with no output instead of 'invalid tag: to do' with exit 2 (reproduced). It also re-normalizes the same tag once per bookmark."},
  {"file":"src/cli.ts","line":56,"summary":"`list --tag` with no value, or with unknown arguments, silently falls back to listing everything.","failure_scenario":"`bm list --tag` (tag forgotten) exits 0 and prints all bookmarks, so the user thinks the filter worked (reproduced)."},
  {"file":"src/cli.ts","line":42,"summary":"Number(rawId) turns '' and ' ' into 0 and accepts '0x1' and '1e0', so malformed ids get past the usage check.","failure_scenario":"`bm tag \"\" work` prints 'no bookmark 0' with exit 1 instead of the usage error with exit 2 (reproduced)."},
  {"file":"src/store.ts","line":56,"summary":"BookmarkStore.tag writes to the console with console.warn on a duplicate tag, although the plan says a duplicate tag is a silent no-op and the store should not print anything.","failure_scenario":"A library or test caller of store.tag(1, 'work') sends unexpected warnings to stderr, and the CLI and store disagree on duplicate handling."},
  {"file":"src/store.ts","line":51,"summary":"tag() looks up the bookmark before validating the tag, so an unknown id plus an invalid tag reports not-found (exit 1) instead of bad input (exit 2), unlike the plan's normalize-first order.","failure_scenario":"store.tag(99, 'to do') throws BookmarkNotFoundError rather than InvalidTagError."},
  {"file":"docs/plans/2026-10-14-bookmark-tags.md","line":100,"summary":"Plan tasks are ticked as done, but the tests they list are missing: duplicate tag and unknown id in the store, unknown id in the CLI.","failure_scenario":"The duplicate and not-found paths had no tests, so the divergent CLI tagging path and the exit-1 mapping were never checked."}
]
```

**What changed:**
- **`src/store.ts`**:
  - Parse errors now propagate instead of being swallowed.
  - `tag()` validates the tag first, no longer prints a warning, and a duplicate is a silent no-op.
  - `listByTag()` normalizes the tag once, before filtering.
- **`src/cli.ts`**:
  - `tag` now goes through `store.tag()`.
  - The id must be all digits (`/^\d+$/`), and extra arguments are rejected.
  - `list` returns `usage: bm list [--tag <tag>]` with exit 2 when `--tag` has no value or when there are stray arguments.
- **`test/store.tags.test.ts`**: added tests for a duplicate tag, an unknown id, and a corrupt file being an error that leaves the file untouched.
- **`test/cli.tags.test.ts`**: added tests for an unknown id (exit 1), a non-numeric id (exit 2), an invalid `--tag` on an empty store (exit 2), and `--tag` with no value (exit 2).

**One behavior change:** a corrupt store file now makes `bm` stop with a raw `SyntaxError` and leaves the file alone, which is how it behaved before this branch. A friendlier error with its own exit code would be a reasonable follow-up.

Files are in <fixture>`:
- `src/store.ts`
- `src/cli.ts`
- `test/store.tags.test.ts`
- `test/cli.tags.test.ts`