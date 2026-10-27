I couldn't reproduce SHOP-312, so I haven't made any changes.

**What I tried**
- **Exact command from the ticket:** `bm add https://example.com 'The "best" tools'` against a scratch `BM_FILE`. It exited 0. The file contains `"title": "The \"best\" tools"`, which is correctly escaped, valid JSON.
- **Other commands on the same file:** `list`, `tag 1 foo` and `list --tag foo` all worked. `tag` rewrites the file, and the quotes survived.
- **Code path:** the file is only written by `BookmarkStore.#write`, via `JSON.stringify`, which escapes quotes. There is no hand-built serialization or CSV-style splitting anywhere in `src/store.ts`, and git history shows no earlier format.
- **Tests and your real file:** `npm test` passes all 15 tests. Your real `~/.bookmarks.json` parses as valid JSON.

**What the ticket leaves open**
- **Reporter's version:** they may be on a different version or a fork. This repo has only three commits.
- **Hand-edited file:** the file may have been edited by hand. A pre-existing bad file would break every command, which could look like a title-with-quotes problem.
- **Shell quoting:** the reporter's shell may have mangled the quoting. In that case the title would be wrong, but the file would still be valid JSON.
- **Different symptom:** the actual error may not be what the ticket describes.

To go further I need the reporter's exact error message, the corrupted file contents, and their `bm` version or commit. I'd rather not guess at a fix.

If you'd like, I can add a regression test that adds a title containing quotes and loads it back. It would lock in the current behavior, and I'd treat it as a guard rather than a fix.