I reviewed the branch, fixed two problems in two commits, and left a few smaller points open. All 15 tests pass, up from 10. There is no lint or type-check script in the repo, so I ran neither. I did not run `npm run bm` by hand, and I did not start a fresh agent to re-review the fixes. The production diff is about 10 lines.

## Fixed
- **A corrupt store file was silently overwritten.**
  - `load()` caught the JSON parse error and returned `[]`, so the next `add` or `tag` saved over the file and wiped the bookmarks. On `main` this threw instead.
  - A new test writes a corrupt file and calls `add`. It failed before the fix and passes now (`994a714`).
- **The CLI bypassed `BookmarkStore::tag`.**
  - `cli.ts` re-implemented tagging with `list`, `find` and `save`. That left `store.tag` unused and untested, and the plan's call chain was not followed.
  - `store.tag` also printed a `console.warn` on duplicate tags, where the plan says a duplicate is a silent no-op.
  - The CLI now calls `store.tag`, and the warning is gone (`63b4049`).
  - I added tests for a duplicate tag, an unknown id, and the CLI's exit 1 and exit 2 paths. The last two were missing.

## Open
- **Corrupt file still crashes.** `bm` now exits with an uncaught `SyntaxError` and a stack trace, as it did before this branch. If you want a friendly message and an exit code, that needs a new error class and a CLI mapping. I recommend doing that as its own change.
- **`bm list --tag` with no value lists every bookmark.** The plan doesn't say what should happen. I recommend a usage error with exit 2, but that changes what users see, so I left it.
- **`BookmarkStore::save` is public and the CLI no longer uses it.** It is still used internally. I left it alone.

## Where to look
1. `src/store.ts`, `load()` to `save()`: confirm a corrupt or unreadable file can never reach `save`.
2. `src/cli.ts`, the `tag` and `list --tag` cases: the CLI should only parse, call the store and print.

The rest (`tags.ts`, `bookmark.ts`, the plan ticks and the tag tests) is routine and can be skimmed.