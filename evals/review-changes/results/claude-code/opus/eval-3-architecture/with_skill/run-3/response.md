I found four problems on `feature/bookmark-tags` and fixed two of them, each with a test written to fail first. All 14 tests pass; the project has no lint or type-check script, so only tests were run. A separate agent reviewed both fixes and found them complete.

**Fixed**
- **A damaged bookmarks file got wiped.** The branch's `load()` treated a file it couldn't parse as empty, so the next `bm add` wrote over it and every bookmark was lost. I reproduced this through the real CLI. It now fails without writing, as it did on `main`. Commit `bc3a0de`.
- **`bm tag` skipped the store's tagging method.** The CLI rewrote the file itself, so `BookmarkStore::tag` was never used. That method also printed a warning on a duplicate tag, but AGENTS.md says only the CLI prints. The CLI now calls the store, and the store no longer prints. I also added the duplicate-tag and unknown-id tests the plan asked for. Commit `fbe964e`.

**Open** (these change what users see, so I left them for you)
- **A damaged file now crashes with a raw stack trace.** AGENTS.md says the CLI maps every error to a message and exit code. I recommend a store error class mapped to something like `cannot read <path>` with exit 2.
- **`bm list --tag` with no tag lists everything with exit 0.** This silently does the wrong thing. I recommend a usage error with exit 2.
- **`bm tag "" work` says `no bookmark 0` with exit 1.** An empty string counts as id 0, so it should be a usage error with exit 2. I'd fix it together with the previous item.

**Where to look**
1. `src/store.ts` `load()` and `save()`: everything that writes the file starts from `load()`, so it decides what happens to a damaged file.
2. `src/cli.ts` `run()` and `dispatch()`: which errors become messages and exit codes, and the three open items above.
3. You can skim `src/tags.ts`, `src/bookmark.ts` and the tests.

Nothing was pushed.