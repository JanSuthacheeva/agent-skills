I didn't create the MR. The branch doesn't match its own plan (`docs/plans/2026-10-14-bookmark-tags.md`) in several places, and the plan marks every task done. You'll probably want to fix these first. Then the description can stay as it is, without the review-guide notes.

1. **Duplicate tags aren't deduplicated.** The plan says re-adding a tag does nothing. `BookmarkStore::tag` in `src/store.ts` adds it again anyway, so `bm tag 1 work` twice stores `["work", "work"]`.
2. **`list --tag` doesn't normalize its argument.** `bm tag 1 Work` stores `work`, but `bm list --tag Work` finds nothing. An invalid tag also just returns an empty list instead of exit 2.
3. **A bare `list --tag` lists everything.** With no value after the flag it silently prints all bookmarks instead of a usage error.
4. **Unknown id exits with 2, not 1** as the plan says.
5. **Method renamed.** The plan's `listByTag` is called `listTagged` in the code.
6. **Tests are missing.** The plan's tests for a duplicate tag and for an unknown id (store and CLI) aren't there.

There's no MR template in the repo and no open MR for this branch. Here's the description as the branch stands now:

---

**Title:** `bm: tag bookmarks and filter list by tag`

```
Bookmarks could only be listed all at once. `bm tag <id> <tag>` now adds a tag to a bookmark, and `bm list --tag <tag>` lists only the bookmarks with that tag.

- Tags are stored on each bookmark in the existing `.bookmarks.json`, not in a separate file. Files written before this change have no `tags` field, and `load()` reads them as `tags: []`, so no migration is needed.
- `normalizeTag` in `src/tags.ts` is the only place that decides what counts as a valid tag (trimmed, lowercased, `a-z0-9-`), so the store and the CLI agree. Invalid tags and unknown ids are thrown as typed errors. `run()` turns them into a message and exit 2.

Review:
1. `bm tag` from `src/cli.ts` `run()` to `BookmarkStore::tag`: tagging the same bookmark twice stores the tag twice, although the plan says it should do nothing.
2. `bm list --tag` in `dispatch()`: the tag isn't normalized, so `--tag Work` finds nothing, and `--tag` with no value lists every bookmark.
3. `BookmarkStore::load` and the older-file test in `test/store.tags.test.ts`: existing store files must still load.
Skim: `src/tags.ts`, the `Bookmark` type, the tests, and the ticked tasks in the plan.
```

---

Should I fix points 1-4 and add the missing tests first? Or do you want to push as is? If so, tell me to push and I'll run `git push -u origin feature/bookmark-tags` and create the MR against `main`.