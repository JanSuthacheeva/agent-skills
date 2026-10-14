The branch had four bugs, and I fixed all of them in one commit, `1f9409c`. I wrote a failing test for each first. All 17 tests pass now (10 before). The repo has no lint or type-check scripts, so I ran none. A second agent re-reviewed the fix commit and found no regressions. Nothing is pushed.

## Fixed
- **Duplicate tags:** `bm tag 1 work` run twice stored `["work","work"]`, but the plan says re-tagging is a no-op. The store now checks before adding.
- **Wrong exit code:** `bm tag 9 x` on an unknown id exited 2, but the plan says 1. The CLI now returns 1.
- **`list --tag` skipped normalization:** `list --tag Work` returned nothing because only `work` is stored, and an invalid tag was never rejected. The CLI and the store now normalize it, and an invalid tag gives `invalid tag: <raw>` with exit 2.
- **`list --tag` with no value:** it silently listed every bookmark. It now prints `usage: bm list [--tag <tag>]` and exits 2. The plan doesn't specify this message, so I picked it.
- **Name mismatch:** the store method was `listTagged`, but the plan names it `listByTag`. I renamed it, and no references to the old name remain.
- **Missing tests:** the plan asks for tests for a duplicate tag, an unknown id and a non-numeric id. I added them.

## Open
- **Existing duplicate tags:** the bug was already live, so any store file written with the old code may hold duplicate tags. I did not clean those up. If you ran the old code against a real `~/.bookmarks.json`, check it by hand or dedupe in `load()`.
- **Double normalization:** the CLI and the store both normalize tags, which is harmless because the result is the same. The plan only asks for it in the CLI, so I left the store call in as a safeguard for other callers. Remove it if you prefer one place.

## Where to look
1. `src/cli.ts`, the `tag` and `list` cases, plus the error mapping at the top: exit codes and messages against the plan.
2. `src/store.ts`, `load()` to `tag()` to `save()`: the file format and the dedupe.

The rest (`tags.ts`, the plan checkboxes, the original tests) is routine and can be skimmed.