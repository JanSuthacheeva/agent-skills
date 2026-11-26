I reviewed `feature/bookmark-remove` against `feature/bookmark-share` and found one real bug, now fixed. All 20 tests pass; the project has no lint or type check to run.

**Something you should know first:** while proving the bug, I ran the CLI without setting `BM_FILE`, so it used your real `~/.bookmarks.json` instead of a temp file. The bug made it save that file again (modified at 16:49 today). It had no bookmark 9, and loading and saving it unchanged keeps every field, so I believe the content is intact: it still holds bookmark 1 with its `tags`. Please check it if it matters to you. Every run after that used a temp file.

**Fixed**
- **Removing an unknown id reported success** (a88abb3). `bm remove 9` printed `removed 9`, exited 0, saved the file anyway (creating it if it was missing) and returned a blank placeholder bookmark. The plan says this should print `no bookmark 9`, exit 1 and leave the file alone. `BookmarkStore.remove()` now throws `BookmarkNotFoundError` before saving, and the existing CLI error handling turns that into the right message and exit code. I added tests at both the store and CLI level; they fail without the fix. The plan's task list was already ticked for "tests for a known and an unknown id", but no such tests existed.
- **Test file name** (9d500c2): renamed `test/remove.test.ts` to `cli.remove.test.ts` to match the other test files.

A separate reviewer agent checked the production fix and found it sound. Its one small note, a test name that claimed more than the test checks, is fixed in 0d500d3, the commit that also adds a `## Review` section to `docs/plans/2026-11-24-bookmark-remove.md`.

**Open:** nothing blocking. If a hand-edited file has two bookmarks with the same id, `remove` deletes both. That was already the case and `add`/`import` never create duplicate ids, so I left it.

**Where to look:** `src/store.ts` `remove()`, where the not-found check must come before `save`. The `remove` case in `src/cli.ts` copies `open` and can be skimmed.

Nothing is pushed.