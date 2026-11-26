I reviewed `feature/bookmark-tags` against `main` and the plan in `docs/plans/2026-10-14-bookmark-tags.md`. I fixed six bugs in two commits; all 18 tests pass and nothing has been pushed.

**Fixed**
- **f4286a8:**
  - Tagging a bookmark twice saved the tag twice (`["work","work"]`); the plan says that should do nothing.
  - The store method was called `listTagged`; I renamed it to `listByTag`, the name in the plan.
  - Added the duplicate-tag and unknown-id store tests the plan asked for.
- **c3c18c8:**
  - `bm tag 99 work` exited with 2; `AGENTS.md` and the plan say "not found" exits with 1.
  - `bm tag` accepted ids like `""`, `0x1` and `1e0` (`""` became id 0); they now give the usage message.
  - `bm list --tag Work` wasn't lowercased or trimmed, so it found nothing; an invalid tag is now rejected too.
  - `bm list --tag` with no tag printed every bookmark; it's now a usage error. I added this case to the plan.

I showed each bug first by running the CLI against a temporary store file, and each fix has a test that failed before it. A separate reviewer re-checked both commits with edge inputs and found nothing wrong.

**Open** (I'd change only the first)
- `list` ignores unknown or extra arguments (`list --bogus`, `list --tag a extra`) and exits 0. I'd make that a usage error, as `add` does.
- If a hand-edited store file has a `tags` value that isn't a list, `tag` and `list --tag` crash. I'd leave it unless people are expected to edit the file by hand.
- `tag 01 x` tags bookmark 1, and very large ids get rounded. Harmless, so I'd leave both.

**Where to look**
1. `src/cli.ts`: the `run()` error handling (which exit code each error gets) and the argument checks in the `tag` and `list` cases.
2. `src/store.ts` `load()`: how files saved before tags existed are read (missing `tags` becomes an empty list).
3. `src/store.ts` `tag()`. The rest (`tags.ts` and the tests) is routine.

**Checks:** 18/18 tests pass at c3c18c8; the project has no lint or type check set up. The security review (`/security-review`, run against `main...HEAD`) found no vulnerabilities. I fixed things before it reported, but it didn't change anything. This summary is also in the plan as a `## Review` section (0bbf31c).