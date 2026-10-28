No merge request exists for this branch, and the repo has no template. Here is the draft. I haven't pushed anything.

**Title:** `SHOP-311 Tags disappear`

**Description:**
```
Every `bm add` rewrote the bookmarks file without any tags, so
`bm list --tag` found nothing after the next add. `toRecord()` predates
tags and never copied them; it now does.

- `tag()` now saves through `save()` like `add()`, instead of building its
  own records. With one write path, a field added to `Bookmark` later
  can't be dropped by one writer and kept by the other.

Review:
1. `toRecord()` through `save()` and `tag()` in `src/store.ts`: every
   write to the file goes through this path now.
2. The two new tests in `test/store.tags.test.ts`.
Skim: the plan under `docs/plans/` and its review notes.

Tags that earlier `bm add` runs already removed cannot be recovered from
the file and have to be added again.
Files saved from now on store `tags: []` for untagged bookmarks. Reading
works with or without the field.

Refs: SHOP-311
```

Do you want me to push `fix/SHOP-311-tags-lost` and create the merge request against `main` on GitLab? Tell me if you'd like the wording changed first.

**Flow summary so far**
- **Commits:** `5135ad8` (fix and regression test), `a6b9e91` (`tag()` through `save()`), `317d64e` (tick the end-to-end box), `ec1f36b` (review notes).
- **Reproduction after the fix:** the last `list --tag work` prints `1  A  https://a.example`.
- **Where to look, from the review:** `src/store.ts`, `toRecord()` through `save()` and `tag()`. The rest is routine.