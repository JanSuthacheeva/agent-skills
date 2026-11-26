I reviewed `feature/bookmark-tags` against the plan and `AGENTS.md`, fixed three bugs and committed each with tests that fail without the fix. A separate agent reviewed the three fixes and found them correct. Nothing is pushed.

**Fixed**
- **Bookmarks could be wiped out (the serious one):** if the store file was damaged, the code read it as an empty list, and the next `add` or `tag` saved over it. I reproduced this with a truncated file and lost everything. A damaged file now raises an error again and is left alone, as it was before this branch. `7c35427`
- **The CLI did the store's job:** `bm tag` added the tag and saved the file itself instead of calling `BookmarkStore.tag`, which `AGENTS.md` and the plan both rule out. It now goes through the store. I also removed the store's `console.warn` on a duplicate tag, since the plan says tagging twice should do nothing. I added the duplicate-tag and unknown-id tests the plan's ticked tasks called for but were missing. `9807688`
- **`bm list --tag` with no tag listed every bookmark** without any error. It now prints `usage: bm list [--tag <tag>]` and exits 2, and the plan lists that error. `9007f9a`

**Open: these need a decision from you**
- **A damaged or empty store file now crashes with a raw stack trace** and exit code 1, which is the code `AGENTS.md` reserves for "not found". No data is lost, but the error message and exit code are something users will see, so I didn't pick them. I recommend a `CorruptStoreError` thrown from `load()` and turned into a clear message with its own exit code in `run()`.
- **The id parsing is loose:** `bm tag ' ' work` is treated as id 0, and `1.0` or `0x1` count as 1. This is minor; checking the id against `/^\d+$/` would close it.

**Where to look**
1. `src/store.ts`, `load()` through `save()`: what a bad file does now.
2. `src/cli.ts`, the `catch` in `run()`: which errors map to which exit codes.
3. Routine, safe to skim: `src/tags.ts`, `src/bookmark.ts` and the tests.

**Checks:** `npm test` passes, 18 of 18, at `9007f9a`. The project has no lint or type check set up. I also added this summary to the plan as a `## Review` section (`98cf7a0`).