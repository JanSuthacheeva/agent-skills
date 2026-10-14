Review done: 4 defects found and fixed in one commit, `d3f0a33`. The suite was green (10 tests) before I started and is green after (15 tests). I did not run a separate fresh-agent review of the fixes. They are about ten changed lines across two source files, and each has a test that failed before the fix. I did not push anything.

**Fixed**
- **Wrong exit code:** `bm tag 9 x` with an unknown id exited 2. The plan and `AGENTS.md` say 1 for not found. A new CLI test failed on the exit code.
- **Duplicate tags:** `BookmarkStore.tag` pushed the tag again every time, so tagging `work` twice stored `["work","work"]`. The plan says it should be a no-op. A new store test failed.
- **Wrong method name:** the store had `listTagged`, but the plan names `listByTag`. I renamed it and updated the existing test.
- **`list --tag` skipped `normalizeTag`:** `--tag " Work "` found nothing, and `--tag "to do"` was not rejected. It now normalizes first, so an invalid tag prints `invalid tag: to do` and exits 2. A new CLI test failed before the change.
- **Missing tests:** the plan asks for tests on a duplicate tag, an unknown id and a non-numeric id. I added them (plus the `list --tag` case above).

**Open**
- `bm list --tag` with no value silently lists everything. The plan doesn't say what should happen. I'd make it a usage error with exit 2, but that is a user-visible choice, so I left it.
- `tag()` normalizes the tag a second time after the CLI already did. That is harmless and arguably good defence, so I left it.

**Where to look**
- `src/store.ts` `tag()`: the only place that writes data. It now ignores duplicates, and it saves the whole file back after `load()`.
- `src/cli.ts` `run()` and the `list` case: the error-to-exit-code mapping and the `--tag` argument parsing.
- Everything else is routine and can be skimmed: `src/tags.ts`, `src/bookmark.ts`, and `load()` reading old files as `tags: []`, which has a test.