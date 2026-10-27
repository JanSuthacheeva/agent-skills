I found the cause of SHOP-311. The reporter's guess is wrong: `list --tag` works fine. Running `bm add` deletes every existing tag.

**Root cause:** `toRecord()` at `src/store.ts:26` doesn't copy `tags` when it writes a bookmark to the file. `save()` writes through it, and `add()` calls `save()` with every bookmark, so each `add` rewrites the whole file without tags. Commit 0b70eb5 ("tag bookmarks and list by tag") worked around this inside `tag()` instead of fixing `toRecord()`, so `tag()` is the only command that keeps tags.

**Evidence:** I ran the real CLI against a scratch file (`BM_FILE`). The steps were `add` → `tag 1 work` → `list --tag work`, which showed the bookmark. The file at that point had `"tags": ["work"]`. After one more `add`, the file had no `tags` key on any bookmark and `list --tag work` printed nothing. It fails every time. No existing test tags a bookmark and then adds another.

**What else is affected:**
- `save()` is public, so anything else that calls it later would lose tags the same way. The same fix covers it.
- Tags are already gone for good in any bookmarks file where someone ran `bm add` after `bm tag`. The fix stops further loss but can't bring them back, because they're no longer in the file.

**Plan:** `docs/plans/2026-10-27-fix-tags-lost-on-add.md`. The fix is to make `toRecord()` include `tags` and have `tag()` call `save()` instead of its own workaround. The first task adds a regression test (tag, then add, then expect the tag to still be there). I wrote down the failure message I expect from that test today but haven't run it.

**Open question:**
1. Should we repair the tags that are already lost? I recommend no code repair, since the data is gone. Instead, tell affected users in the ticket to re-tag their bookmarks or restore `~/.bookmarks.json` from a backup.

I didn't change any code or commit anything; the only new file is the plan under `docs/`.