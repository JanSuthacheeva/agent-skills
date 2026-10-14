I've read the diff and the plan, so here is the draft. Three places in the code differ from the plan, and I haven't pushed anything.

```
bm: add tag command and list --tag
```

```
Bookmarks could not be grouped or filtered. `bm tag <id> <tag>` now adds a
tag to a bookmark and `bm list --tag <tag>` lists the bookmarks that have it.

- Tags live on each bookmark in the existing store file, so there is no
  migration. Files written before this change have no `tags` field and
  `load()` reads them as `tags: []`.
- Tags are normalized once in `normalizeTag` (trimmed, lowercased, only
  `a-z`, `0-9` and `-`), so the store and the CLI agree on what a valid tag is.

Review:
1. `src/store.ts`: `load()` defaulting missing `tags`, and `tag()`, which
   rewrites the whole file. Check the old-file path and what `tag()` does for
   a tag the bookmark already has (it is appended again).
2. `bm tag` and `bm list --tag` from `run()` in `src/cli.ts`: the new
   try/catch wrapper that maps `InvalidTagError` and `BookmarkNotFoundError`
   to messages and exit codes, and `listTagged` (the `--tag` value is not
   normalized before the lookup).
Skim: `src/tags.ts`, the `Bookmark` type, the tests, the ticked tasks in the plan.

Differences from `docs/plans/2026-10-14-bookmark-tags.md`:
- `listByTag` is named `listTagged`.
- An unknown id exits 2; the plan and AGENTS.md say 1 for not found.
- Tagging with an existing tag appends a duplicate; the plan says no-op.
```

Before you use it:
- **Plan differences:** these look like bugs, not decisions. I found no reason for them in the commits or the plan, so I didn't invent one. Either fix them (exit 1, skip duplicates, normalize the `--tag` value so `list --tag Work` finds `work`) or tell me why they're intended and I'll rewrite that list as decisions.
- **Reading order:** the Review section follows my own read of the diff, since no earlier review left a "where to look" list.
- **Deploy:** there are no steps, so I left the section out.
- **Ticket:** the branch name has no ticket ID, so there is no `Refs:` line.
- **Existing MR:** none is open for this branch.

Say the word if you want me to push and create it.