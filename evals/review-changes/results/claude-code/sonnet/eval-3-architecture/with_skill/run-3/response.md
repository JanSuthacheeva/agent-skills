I reviewed `feature/bookmark-tags` against the plan and fixed four problems in two commits. Tests went from 10 to 17 and all pass. I didn't run lint or type checks, because the repo has no scripts for them. Nothing is pushed.

**Fixed**
- **Corrupt store file wiped:** `load()` caught JSON errors and returned `[]`, so the next `add` or `tag` overwrote the corrupt file. I reproduced it with `bm add` against a truncated file, which replaced it with a one-item list. `load()` now throws again, and a test checks the file stays untouched. Commit `cab29a7`.
- **`list --tag` skipped validation on an empty store:** `listByTag` only validated the tag inside the filter, so `list --tag "to do"` on an empty store returned nothing instead of exit 2. It now validates first. Commit `cab29a7`.
- **`tag` command bypassed the store:** the CLI reimplemented tagging with `list()` and `save()`, leaving `BookmarkStore.tag` unused. The plan says the store owns tagging. The CLI now calls `store.tag`. I also removed the `console.warn` on a duplicate tag, because the plan says it is a silent no-op. Commit `db92498`.
- **`list --tag` with no value:** it silently listed everything. It now prints `usage: bm list [--tag <tag>]` and exits 2. Commit `db92498`.
- **Missing tests:** I added tests for an unknown id (store and CLI), duplicate tags, a non-numeric id, and the cases above. They are in the same commits.

A fresh agent reviewed the two production-code commits and found no regressions. It did raise three small points, listed below.

**Open**
- **Corrupt file error:** a corrupt file now reaches the user as a raw `SyntaxError` stack trace, because `run()` rethrows unknown errors. The data is safe, but I'd add a store error class and map it in the CLI. That adds user-visible behaviour, so I left it for you.
- **Trailing arguments:** `bm list --tag work extra` is accepted silently. It is minor, and I'd reject extra arguments.
- **Empty id:** `bm tag "" work` gives `Number('')` = 0 and reports `no bookmark 0` with exit 1 instead of a usage error. It was in the original code, and I'd fix it separately.
- **Plan file:** its last task (the manual `npm run bm` check) is ticked, but nothing in the branch shows it was done. I ran that flow myself and it works.

**Where to look**
1. `src/store.ts`, `load()` to `save()`: what happens to a corrupt file. This is the part that carries real risk.
2. `src/cli.ts`, the `tag` and `list` cases and the error mapping in `run`: how errors become exit codes.
3. Everything else, such as `src/tags.ts`, `src/bookmark.ts` and the tag tests, is routine and can be skimmed.