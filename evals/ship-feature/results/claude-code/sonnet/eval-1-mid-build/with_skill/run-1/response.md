The branch is built and reviewed, and no merge request exists yet. I haven't pushed anything. The draft is below.

**Title**
`bm: tag bookmarks and filter the list by tag`

**Description**
```
Bookmarks could not be grouped. `bm tag <id> <tag>` now adds a tag to a bookmark and `bm list --tag <tag>` lists the bookmarks with that tag.

- Tags are normalized once in `normalizeTag` (trimmed, lowercased, only `a-z`, `0-9` and `-`), and the CLI does this before calling the store. The store therefore trusts its input, and the CLI and store cannot disagree on what a valid tag is.
- The store file keeps its format. `load()` reads bookmarks written before this change as `tags: []`, so no migration is needed.
- Tagging a bookmark with a tag it already has is a no-op, not an error. The file is not rewritten in that case.
- Ids are validated as decimal digits only. `Number()` accepted `""`, `0x1` and `1e0`, so `bm tag "" work` reported "no bookmark 0" instead of the usage error.

Review:
1. `src/store.ts`, `load()` to `tag()` and `listByTag()`: old files load as `tags: []`, duplicates are skipped, and the file is saved only when something changed.
2. `bm tag` from `run()` in `src/cli.ts`: argument parsing, the id check, and how `report` maps `InvalidTagError` to exit 2 and `BookmarkNotFoundError` to exit 1.
Skim: `src/tags.ts`, the `tags` field on `Bookmark`, and the tests.

Left out: removing a tag and listing all known tags.
```

I didn't read a reason for the last line, so the "Left out" item is a guess from the plan. The plan doesn't mention removal or a tag list. I can drop that line if you'd rather not claim it.

Should I push the branch and create the merge request on GitLab with this title and description?