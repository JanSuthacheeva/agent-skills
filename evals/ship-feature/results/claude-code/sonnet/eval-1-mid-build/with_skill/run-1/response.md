The build and the review are finished. The merge request is drafted but not pushed, and no MR exists for this branch yet.

**Where it stands**
- Build: all 5 plan tasks are done and ticked, and 19 of 19 tests pass. I confirmed the commits match the ticked boxes.
- Review: an isolated agent found and fixed two small bugs. `bm list --tag` with no tag now exits 2 with a usage message. `bm tag "" work` now gives the usage error instead of `no bookmark 0`. Nothing is left open.
- One caveat from the review: the fixes were re-read by the reviewer, not reviewed by a second agent.

**Proposed title**
`bm: add tags to bookmarks`

**Proposed description**
```
Bookmarks could not be grouped or filtered. Each bookmark now carries tags:
`bm tag <id> <tag>` adds one and `bm list --tag <tag>` filters by it.

- Tags are normalized in one place (`normalizeTag`: trimmed, lowercased,
  only `a-z`, `0-9` and `-`), so the store and the CLI agree on what a
  valid tag is. The store normalizes again, so direct callers cannot save
  a bad tag.
- Tags live in the existing store file as a `tags` field. Older files
  without it load as `tags: []`, so no migration is needed.
- Tagging with a tag the bookmark already has is a no-op, not an error.
- Exit codes follow the existing convention: 1 for an unknown id, 2 for an
  invalid tag or bad usage.

Review:
1. `src/store.ts` `load()` and `tag()`: legacy files without `tags` are
   read as `[]` and only rewritten with `tags` on the next save. A corrupt
   file throws instead of being read as empty, so nothing is overwritten.
2. `bm tag` and `bm list --tag` from `src/cli.ts` `dispatch` through
   `BookmarkStore::tag` and `listByTag`: check the error paths and exit
   codes.
Skim: `src/tags.ts` and the tests.

Left out: argument parsing is hand-rolled, so an unknown flag such as
`list --tga work` is still ignored and lists everything. This needs a
decision if more options arrive.
```

Should I push `feature/bookmark-tags` and open the merge request against `main`? Tell me to push, or tell me what to change in the title or description first.