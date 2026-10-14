```json
[
  {"file": "src/store.ts", "line": 27, "summary": "load() catches JSON parse errors and returns [], so the next write replaces a corrupt or half-written store file and all bookmarks are lost.", "failure_scenario": "Truncated .bookmarks.json, then `bm add https://b.dev B` printed `added 1` and the file then held only the new bookmark (reproduced). Before this branch the parse error was thrown."},
  {"file": "src/cli.ts", "line": 47, "summary": "The `tag` command copies the store's tagging logic inline (list, mutate, store.save) instead of calling BookmarkStore.tag, so store.tag is never used in production.", "failure_scenario": "Breaks the AGENTS.md rule \"The CLI never touches the file directly\" and the plan's call chain `run -> BookmarkStore::tag`. Duplicate-tag and not-found rules now live in two places that can drift apart."},
  {"file": "src/store.ts", "line": 65, "summary": "listByTag calls normalizeTag inside the filter, so an invalid tag only raises an error when the store has bookmarks, and the tag is re-normalized for every bookmark.", "failure_scenario": "On an empty store, `bm list --tag \"to do\"` exits 0 instead of 2 with `invalid tag` (reproduced)."},
  {"file": "src/cli.ts", "line": 57, "summary": "`list --tag` with no value, or any unknown flag, silently lists every bookmark.", "failure_scenario": "`bm list --tag` printed all bookmarks and exited 0 (reproduced). Expected a usage error with exit 2."},
  {"file": "src/cli.ts", "line": 42, "summary": "Number(rawId) accepts '', whitespace and hex, so an invalid id becomes 0 or some other number instead of a usage error.", "failure_scenario": "`bm tag \"\" work` printed `no bookmark 0` and exited 1 instead of usage with exit 2 (reproduced). `bm tag 0x1 work` tags bookmark 1."},
  {"file": "src/store.ts", "line": 56, "summary": "BookmarkStore.tag writes to console.warn on a duplicate tag, which skips the injected Output and goes against the plan, where tagging twice is a no-op.", "failure_scenario": "Once the CLI uses store.tag, `bm tag 1 work` run twice writes a stray warning to stderr that the Output abstraction and tests cannot capture."},
  {"file": "test/store.tags.test.ts", "line": 25, "summary": "The plan's tasks are ticked, but the promised tests for a duplicate tag, an unknown id (store and CLI) are missing.", "failure_scenario": "The duplicated tagging logic in cli.ts and the store's not-found path had no test coverage, so the bugs above went through."}
]
```

**Fixed** (all 17 tests pass; I also re-ran the CLI by hand against a temp store):
- `src/store.ts`:
  - Removed the try/catch in `load()`, so a corrupt file throws again instead of being overwritten.
  - Removed the `console.warn` in `tag()`.
  - `listByTag()` now normalizes the tag once, before filtering.
- `src/cli.ts`:
  - `tag` now runs `normalizeTag` and then `store.tag(id, tag)`, so the CLI no longer touches the file.
  - The id must be all digits (`/^\d+$/`), otherwise it prints the usage error.
  - `list` rejects a bare `--tag` or an unknown argument with `usage: bm list [--tag <tag>]` and exit 2.
- Added tests:
  - CLI: unknown id, non-numeric id, `list --tag` with no tag, and an invalid tag on an empty store (`test/cli.tags.test.ts`).
  - Store: duplicate tag, unknown id, and a corrupt file (`test/store.tags.test.ts`).

**Behavior change to note:** plain `bm list foo` now exits 2. Before, extra arguments to `list` were ignored.

**Skipped:** nothing. The changes are not committed: your CLAUDE.md says to commit with the `/commit` skill, and it isn't available in this session.

Changed files are in <fixture>`:
- src/cli.ts
- src/store.ts
- test/cli.tags.test.ts
- test/store.tags.test.ts