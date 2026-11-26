I fixed three bugs on `feature/bookmark-tags`, each with a test that fails without the fix. The worst one could delete all of a user's bookmarks. Nothing has been pushed.

## Fixed
- **Corrupt store file wiped out** (8f0c010): if `~/.bookmarks.json` couldn't be parsed, `load()` treated it as empty, and the next `add` or `tag` saved over it. I reproduced it: a truncated file holding bookmark 1 was replaced by a file holding only the new bookmark. `load()` now throws the parse error, so the file is left alone.
- **`bm tag` bypassed the store** (620f0bd): the CLI repeated the tagging logic and saved the file itself instead of calling `BookmarkStore.tag`, which `AGENTS.md` forbids. `BookmarkStore.tag` also printed a `console.warn` when a bookmark already had the tag, but the plan says that should do nothing. I also added the tests the plan asks for: duplicate tag, unknown id and non-numeric id.
- **Invalid tag accepted on an empty store** (e010c0d): `list --tag "to do"` exited 0 instead of 2, because the tag was only checked inside the filter.

## Open (these change what users see, so they're your call)
- **Corrupt or empty store file:** it now stops with a raw `SyntaxError` stack trace and exit code 1, which is also the "not found" code. `main` behaves the same way. I'd add a `CorruptStoreError` with a clear message and its own exit code.
- **`bm list --tag` with no value:** it lists every bookmark and exits 0. I'd show the usage message and exit 2.
- **`bm tag "" work`:** it prints `no bookmark 0` and exits 1, because `Number('')` is 0. I'd treat it as a usage error.

## Where to look
1. `src/store.ts`, from `load()` to `save()`: what happens when the file is corrupt.
2. `src/cli.ts`, the error handling in `run()`.

`src/tags.ts` and the tests are routine and can be skimmed.

## Checks
- `npm test` passes at e010c0d (18 of 18). The project has no lint or type-check script.
- `/security-review` found no vulnerabilities. It flagged the data loss and the duplicated `tag` logic, which are fixed above.
- A separate agent reviewed the three fixes. It raised the empty-file behaviour, which matches `main` and is listed under Open.
- The plan now ends with a `## Review` section holding this summary (775abd5).