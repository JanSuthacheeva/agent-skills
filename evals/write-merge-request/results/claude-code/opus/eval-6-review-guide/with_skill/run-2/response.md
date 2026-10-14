I checked for an open MR on `feature/bookmark-tags` and there isn't one. Here is the draft. Nothing is pushed or created yet.

**Title**

```
bm: tag bookmarks and filter list by tag
```

**Description**

```
Bookmarks could only be listed as one flat list. This adds `bm tag <id> <tag>`
to tag a bookmark and `bm list --tag <tag>` to list only the bookmarks with
that tag, following `docs/plans/2026-10-14-bookmark-tags.md`.

- Tags are stored on each bookmark in the existing `.bookmarks.json`, so the
  file keeps its format. `load()` reads files written before this change as
  `tags: []`, so no migration is needed.
- Tags are normalized in one place, `normalizeTag` (trimmed, lowercased,
  only `a-z`, `0-9` and `-`), so the store and the CLI agree on what a valid
  tag is.
- `BookmarkStore` owns tagging and filtering. The CLI only parses, prints
  and maps `InvalidTagError` / `BookmarkNotFoundError` to exit code 2 in
  `run()`.

Review:
1. Store data: `BookmarkStore::load` (how old files are read) and
   `BookmarkStore::tag` (load, change, save the whole file). Check what
   happens to existing bookmarks and to tags the bookmark already has.
2. `bm tag` and `bm list --tag` from `src/cli.ts` `run()` to the store:
   argument parsing, where the tag is normalized, and how errors become
   exit codes.
Skim: `src/tags.ts`, the `Bookmark` type, the tests and the plan checkboxes.
```

I left out a Deploy section because nothing outside the code changes.

Before you open this, the code doesn't match the plan in several places. These are the spots a reviewer will hit in step 1 and step 2:

1. **Duplicate tags:** the plan says re-adding a tag the bookmark already has does nothing. Instead, `BookmarkStore::tag` (`src/store.ts:50`) adds it a second time. The planned test for this case is missing.
2. **`list --tag` isn't normalized:** the tag goes into `listTagged` as typed, so `bm list --tag Work` finds nothing even though `bm tag 1 Work` saved it as `work`. The plan says to normalize it.
3. **Unknown id exit code:** the plan says exit 1, but the code exits 2. The planned CLI test for an unknown id is also missing.
4. **`list --tag` with no value** quietly lists every bookmark instead of showing a usage error.
5. **Method name:** the method is called `listTagged`, but the plan calls it `listByTag`.

The plan marks all of its tasks as done, so the missing tests weren't flagged anywhere. Should I fix these on the branch first? If so, I'll update the description to match. Otherwise, tell me to push and I'll create the MR with the draft as it is.