**Root cause:** `toRecord()` in `src/store.ts:25` leaves `tags` out of the stored record. `add()` rewrites the whole file through `save()` (`src/store.ts:59`, `:66`), so every `bm add` wipes all existing tags. `list --tag` itself is fine. Commit 0b70eb5 introduced this: it added tags, but `tag()` worked around `toRecord()` by hand and `toRecord()` never got `tags`.

**Evidence:**
- I ran the real CLI against a scratch `BM_FILE`. After `add`, `add`, `tag 1 work` and `tag 2 work`, `list --tag work` showed both bookmarks.
- After one more `bm add`, `list --tag work` printed nothing.
- The file contents confirmed it: `tags` were present before the last add and missing from all three records after it.

**Also affected:** any future caller of `save()` would lose tags the same way. Real bookmark files where someone ran `bm add` after tagging have already lost those tags, and they can't be recovered from the file.

**Plan:** `docs/plans/2026-10-27-fix-tags-lost-on-add.md`. It is the only change to the working tree, and I committed nothing.

**Open question:**
1. Should we repair tags that were already lost? I recommend no, because they can't be recovered, so just tell users to re-tag.