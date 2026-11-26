I reviewed `feature/bookmark-tags` against `main` and its plan, and fixed four bugs, one of which lost data. All 19 tests pass and nothing is pushed. Before each fix I reproduced the bug with the real CLI and wrote a test that failed, and a separate agent reviewed the fix commits.

**Fixed**
- **Data loss:** if the bookmarks file was corrupt, `load()` silently treated it as empty. The next `add` overwrote it with a single bookmark and the rest were gone; I reproduced this. The parse error now gets through, as it did on `main`. (`cdd546b`)
- **Store bypassed:** `bm tag` did the tagging itself with `list()` and `save()`, so `BookmarkStore::tag` was never used. That breaks the plan and AGENTS.md (the store owns the file). The store also printed a warning when a bookmark already had the tag, where the plan says that should do nothing. (`30189c9`)
- **Invalid tag accepted:** with no bookmarks saved, `bm list --tag 'to do'` exited 0 instead of 2, because the tag was only checked inside the filter. (`10a6817`)
- **Bad arguments:**
  - `bm tag '' work` printed `no bookmark 0` with exit 1 instead of the usage error.
  - `bm list --tag` with no tag listed every bookmark.

  Both now print usage and exit 2, and the plan's error list says so. (`e62d11a`)

I also added the tests the plan asked for but the branch lacked: a duplicate tag and an unknown id.

**Open (your call)**
- **Crash on a bad file:** a corrupt, empty or non-array bookmarks file makes the CLI crash with a stack trace and exit 1. That's how `main` behaves too, but AGENTS.md says the CLI turns errors into messages and exit codes. I'd add a `CorruptStoreError` that the CLI prints as a message, and treat a 0-byte file as empty. I didn't do it because it adds a new user-visible error.
- **`--tag` ignored:** `bm list foo --tag work` lists everything, because only the first argument is checked. Low risk.

**Where to look**
1. `src/store.ts`, from `load()` to `save()`: what happens when the file can't be read.
2. `src/cli.ts`, `run()` and `dispatch()`: how errors become exit codes, and the argument checks for `tag` and `list`.
3. Routine, can be skimmed: `tag()` and `listByTag()` in the store.

**Checks:** `npm test` passes at `e62d11a`. The project has no lint or type-check step. I added this summary to the plan as a `## Review` section (`aec452f`).