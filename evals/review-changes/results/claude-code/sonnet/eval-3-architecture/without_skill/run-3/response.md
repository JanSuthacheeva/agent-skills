I reviewed the branch and fixed everything I found, in one commit (`11634ed`). All 14 tests pass, and a manual `add`, `tag`, `list --tag` run against a temp store file behaved correctly. I committed with plain git because the `/commit` skill isn't available here.

What I fixed:

1. **CLI bypassed the store.** `bm tag` in `src/cli.ts` loaded, mutated and saved bookmarks itself, which breaks the rule that the CLI never touches the file and ignored `BookmarkStore.tag`. It now calls `store.tag`.
2. **Corrupt store file wiped data.** `load()` returned `[]` on a JSON parse error, so the next `add` or `tag` would overwrite the file and lose every bookmark. I removed the try/catch, so a corrupt file now throws.
3. **Duplicate tag warning.** `store.tag` printed a `console.warn` on a duplicate tag, but the plan says a duplicate is a silent no-op. I removed the warning.
4. **`list --tag` with no value.** It silently listed everything. It now prints `usage: bm list [--tag <tag>]` and exits 2.
5. **Missing tests.** The plan's checked-off tasks promised tests for a duplicate tag and an unknown id, and they didn't exist. I added them at both store and CLI level, plus one for the `list --tag` usage error.

I also made `listByTag` normalize the tag once instead of once per bookmark.

The `bm tag` handler still uses `normalizeTag` itself so it can print the normalized tag, as the plan's call chain describes.