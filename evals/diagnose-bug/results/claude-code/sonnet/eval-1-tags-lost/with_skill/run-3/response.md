**Root cause:** `toRecord()` at `src/store.ts:26` leaves out `tags`. `add()` (`src/store.ts:60`) writes every existing bookmark back through `save()`, which uses `toRecord()`, so each `bm add` erases the tags already on disk. `list --tag` is fine. It reads data that no longer has tags. Commit 0b70eb5 added tags to the model but not to `toRecord()`.

**Evidence:**
- I ran `add`, `tag 1 work`, `list --tag work`, `add`, `list --tag work` against a scratch `BM_FILE`.
- The first `list --tag work` shows bookmark 1. After the second `add`, it prints nothing.
- The file has `"tags": ["work"]` after `tag` and no `tags` key after the second `add`.
- This fails on every run.
- `tag()` at line 74 avoids the bug by writing `tags` itself.

**Also affected:**
- `save()` is public and loses tags for any caller. The same fix covers it.
- Any `.bookmarks.json` where a bookmark was tagged and then another was added has already lost those tags. They can't be recovered from the file.

**Plan:** `docs/plans/2026-10-27-fix-tags-lost-on-add.md`. It is the only change in the working tree, and nothing is committed.

**Open question:**
1. Repair the tags already lost? I recommend no, since the data is gone. Tell the reporter to re-tag.