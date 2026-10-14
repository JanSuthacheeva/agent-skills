I've implemented the bookmark tags plan in four commits plus one that checks off the tasks in the plan file. All 22 tests pass (13 of them new). I also ran `npm run bm` end to end against a temp store file, and the output and exit codes matched the plan:

- `bm tag 2 " Runtime "` prints `tagged 2 runtime`, and tagging it again with the same tag changes nothing.
- An unknown id prints `no bookmark 9` and exits 1. A non-numeric id prints the usage line and exits 2. An invalid tag prints `invalid tag: to read` and exits 2.
- `bm list --tag runtime` prints only the matching bookmarks, in the same format as `list`.
- A store file written before tags existed (no `tags` field) loads fine and can be tagged without any migration.

**Additions not in the plan:**
- **Store checks tags too:** `BookmarkStore::tag` and `listByTag` call `normalizeTag` themselves, as well as the CLI doing it. That way any caller of the store gets the guarantee that saved tags are valid, not just the CLI. It's harmless because normalizing an already-normalized tag returns it unchanged.
- **New `list` usage error:** `bm list --tag` with no value, or with unexpected extra arguments, prints `usage: bm list [--tag <tag>]` and exits 2. Before this, `list` silently ignored any arguments.
- **Extra arguments to `tag`:** `bm tag` with more than two arguments also prints its usage line and exits 2.

The `/commit` skill isn't installed in this environment, so I committed with `git commit` directly and followed the repo's existing message style.