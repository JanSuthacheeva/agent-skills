I reviewed `feature/bookmark-remove` against `feature/bookmark-share` and fixed one real bug. All 19 tests pass.

**Fixed**
- **Removing an id that doesn't exist reported success and wrote the file.** I ran `bm remove 9` on a store without that bookmark: it printed `removed 9`, exited 0, and saved the file, creating it if it was missing. The plan says it should print `no bookmark 9`, exit 1, and leave the file alone. `remove()` in `src/store.ts` now raises the not-found error before saving anything, which is what the plan describes.
- **Missing tests.** The plan's tests for removing an existing and an unknown id in the store were never written. I added them, plus a test that the file isn't created. The three unknown-id tests failed before the fix. I also split `test/remove.test.ts` into `store.remove.test.ts` and `cli.remove.test.ts` to match the other test files.

Both are in commit a90d83f. A separate agent reviewed the fix and found no problems.

**Not fixed: needs your call**
- **The id check accepts too much.** `remove` reads the id the same way `open` already does on the base branch:
  - `bm remove ""` says `no bookmark 0` with exit 1. The plan says a non-integer should get the usage message with exit 2.
  - `bm remove 0x1` and `bm remove 1e0` both delete bookmark 1.

  I left this alone because it changes what the commands accept, and the code comes from the base branch. I recommend one strict parser that accepts digits only, used by both `open` and `remove`, ideally fixed on `feature/bookmark-share` first.

**Where to look**
1. `remove()` in `src/store.ts`: it now stops before saving when the id isn't found.
2. The `remove` case in `src/cli.ts`: the id check described above.
3. The tests are routine and can be skimmed.

**Checks:** all tests pass as of commit a90d83f. The project has no lint or type-check setup, so tests are the only check. I also added a `## Review` section with this summary to the plan and committed it (1a7af4b). Nothing has been pushed.