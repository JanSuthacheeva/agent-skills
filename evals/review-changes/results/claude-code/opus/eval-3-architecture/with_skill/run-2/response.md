I reviewed `feature/bookmark-tags` against its plan and fixed four bugs, each in its own commit with a test that fails without the fix. All 18 tests pass, the project has no lint or type checks to run, and I ran the CLI end to end against a temp store. A separate agent reviewed the fix commits and confirmed each one works.

I committed with plain git because the `/commit` skill isn't installed in this environment. Nothing is pushed.

**Fixed**
- **Data loss:** if the store file was corrupt, `load()` returned `[]`, and the next `bm add` wrote over the file and wiped every bookmark. The command now fails and leaves the file alone, which is how `main` behaves - `6c5f972`.
- **Wrong layer:** the CLI `tag` command re-did tagging with `list()`/`save()` instead of calling `BookmarkStore::tag`, so the store method wasn't used by the app. `store.tag` also printed a warning from inside the store when a bookmark already had the tag; the plan says that case should do nothing. The CLI now calls `store.tag`, and the warning is gone - `e34ec89`.
- **Invalid tag accepted:** `bm list --tag "to do"` exited 0 when the store was empty, because the tag was only checked while filtering bookmarks. It now prints `invalid tag: to do` and exits 2 - `e055c73`.
- **Wrong error for a bad id:** `bm tag "" work` printed `no bookmark 0` and exited 1, and `0x1` was accepted as id 1. Ids must now be plain digits; anything else gets the usage message and exit 2, as the plan says - `14dc3d5`.
- I also added the tests the plan's tasks list but the branch didn't have: tagging twice, an unknown id in the store and in the CLI, and the CLI going through `store.tag`.

**Open** (left alone because they change what users see)
- **Corrupt store crashes:** a corrupt store file now ends in a raw `SyntaxError` with a stack trace, and a file holding JSON that isn't a list gives a `TypeError`. I recommend a `StoreCorruptError` that the CLI turns into a one-line message and exit code, which is how AGENTS.md says errors should work.
- **`list --tag` with no value:** it quietly lists every bookmark, and so does any unknown option. I recommend the usage error with exit 2.
- **Very large ids:** an id like `99999999999999999999` passes the new check and prints a rounded "no bookmark" message. This is minor.

**Where to look**
1. `src/store.ts` `load()` through `add()`/`tag()`: what happens when the file on disk is bad. This is the only place stored data is at risk.
2. `src/cli.ts`, the `tag` and `list` cases: argument parsing, and the fact that the CLI now only parses and prints.
3. `src/cli.ts` `run()`: how errors map to messages and exit codes. Any new error type has to be added here.

You can skim `src/tags.ts`, `src/bookmark.ts` and the test files; they're routine.