I found one real bug in the `remove` command your branch adds on top of `feature/bookmark-share`, and fixed it. The 19 tests pass at `c2560bc`. The project has no lint or type check.

**What was wrong:** running `bm remove` with an id that doesn't exist did nothing to stop it. `bm remove 9` rewrote the bookmarks file, printed `removed 9`, exited 0 and returned a fake empty bookmark. Your plan says this should print `no bookmark 9`, exit 1 and leave the file alone. I showed this with three new tests that failed before the fix. The store tests your plan lists for a known and an unknown id were also missing.

**Fix:** `BookmarkStore::remove` in `src/store.ts` now throws `BookmarkNotFoundError` before it saves anything. The CLI already turns that error into `no bookmark <id>` and exit 1.
- **`6e64711`** — the fix, plus the missing store tests and a CLI test for an unknown id.
- **`c2560bc`** — a fresh agent checked the fix and confirmed it. It also noticed I had changed how `remove` handles a file with duplicate ids, which wasn't needed, so I put the original behaviour back.

**Also checked, nothing to fix:** an id that isn't a number exits 2 with the usage message. `remove ""` and `remove -1` report not-found, the same way `open` does. Removing the same id twice reports not-found the second time. A corrupt file errors out without being overwritten.

**Where to look:** `BookmarkStore::remove` in `src/store.ts` — make sure the throw comes before `save`. The rest is routine.

**Open:** nothing.

I also wrote a `## Review` section into `docs/plans/2026-11-24-bookmark-remove.md` (`1c35392`). Nothing has been pushed.