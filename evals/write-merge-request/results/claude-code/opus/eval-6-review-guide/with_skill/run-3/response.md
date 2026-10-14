I found five places where the branch doesn't match its plan (`docs/plans/2026-10-14-bookmark-tags.md`), even though every task box there is ticked. I'd fix these before opening the MR, because the description below would otherwise promise behaviour the code doesn't have:

1. **Tagging twice saves the tag twice.** The plan says tagging a bookmark with a tag it already has should do nothing. `BookmarkStore::tag` (`src/store.ts:50`) pushes the tag without checking, so `bm tag 1 work` run twice stores `["work", "work"]`.
2. **`list --tag` doesn't normalize the tag.** `src/cli.ts:53` passes the raw value to `listTagged`, so `bm list --tag Work` finds nothing after `bm tag 1 Work`. The plan calls `normalizeTag` here.
3. **Missing tag value lists everything.** `bm list --tag` with no value silently lists all bookmarks instead of printing a usage error.
4. **Unknown id exits with the wrong code.** It exits 2, but the plan says 1.
5. **Tests are missing and a method was renamed.** The plan's tests for a duplicate tag and an unknown id are not in the branch. `listByTag` is called `listTagged` in the code.

There's no open MR for `feature/bookmark-tags` yet. Here is the draft:

---

**Title**

```
bm: tag bookmarks and filter list by tag
```

**Description**

```
Bookmarks could only be listed all at once. They can now carry tags: `bm tag <id> <tag>` adds one, `bm list --tag <tag>` shows only the bookmarks that have it.

- Tags are stored on each bookmark in the existing `.bookmarks.json` instead of a separate file. Older files have no `tags` field, and `load()` reads them as `tags: []`, so there is no migration.
- All tag rules live in `normalizeTag` (trimmed, lowercased, only `a-z`, `0-9` and `-`), so the store and the CLI agree on what a valid tag is.
- `BookmarkStore` handles tagging and filtering. The CLI only parses arguments and turns `InvalidTagError` and `BookmarkNotFoundError` into messages and exit codes in a wrapper around `run()`.

Review:
1. Store data: `BookmarkStore::load` filling in missing tags for older files, and `tag()` changing the loaded bookmark and saving the whole list (commit 89c9a04).
2. `bm tag` from `src/cli.ts` `run()` to `BookmarkStore::tag`: argument checks, and which errors get a message and exit code and which are rethrown (commit 22ea159).
Skim: `src/tags.ts` and the tests.

Plan: docs/plans/2026-10-14-bookmark-tags.md
```

---

There's no Deploy section because the branch adds no environment variables, dependencies or migrations, and old store files load as they are. There's also no ticket ID in the branch name, so I left out `Refs:`.

Should I fix the five issues first? If you'd rather open the MR as it is, I'll add them to the description as known gaps. Either way, tell me when to push and create it.