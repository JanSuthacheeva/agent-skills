I reviewed `feature/bookmark-tags` against `main`, using the plan and `AGENTS.md` as the spec. I found six problems, reproduced each one through the real CLI (`npm run bm` with a temp store file), fixed them and committed the fixes in two commits. All 17 tests pass, and I re-ran the CLI to confirm each fix.

**What I fixed**

1. **A corrupt store file wiped all bookmarks (data loss).** `load()` caught JSON errors and returned `[]`, so the next `add` replaced the whole file with one bookmark. I reproduced this: a corrupt file holding bookmark 1 became a file holding only the new one. `load()` now throws on a corrupt file again, as it did on `main`, and the file is left alone.
2. **`bm tag` broke the design.** The CLI loaded the bookmarks, changed them and called `store.save()` itself. That copies the logic in `BookmarkStore::tag`, goes against "The CLI never touches the file directly" in `AGENTS.md`, and ignores the plan, which says `run` should call `BookmarkStore::tag`. It now calls `store.tag()`.
3. **`store.tag` printed a warning.** It called `console.warn` when a bookmark already had the tag. The store shouldn't print, and the plan says tagging twice does nothing. It now returns quietly.
4. **`list` accepted bad arguments.** `bm list --tag` with no value and typos like `bm list --tga work` printed every bookmark and exited 0. Both now print `usage: bm list [--tag <tag>]` and exit 2.
5. **`bm tag '' work` gave the wrong error.** `Number('')` is `0`, so it printed `no bookmark 0` and exited 1 instead of a usage error. The id must now be all digits, which also rejects `1.5` and `-1`. A stray extra argument is now a usage error too.
6. **Tests ticked off in the plan didn't exist.** The plan's checklist claimed tests for a duplicate tag and an unknown id (store and CLI), but there were none. I added those, plus tests for a non-numeric id, bad `list` arguments, an invalid tag on `list --tag` and a corrupt file.

I also changed `listByTag` to normalize the tag once instead of once per bookmark.

**Still open:** a corrupt store file now ends in an uncaught `SyntaxError` with a stack trace. That's the same as on `main`, and the data is safe. The fix that fits `AGENTS.md` would be a `StoreCorruptError` that the CLI turns into a short message. That changes how the CLI behaves for users, so I left it for you to decide.

The `/commit` skill isn't available in this session, so I wrote the commit messages by hand in the repo's `bm: ...` style.