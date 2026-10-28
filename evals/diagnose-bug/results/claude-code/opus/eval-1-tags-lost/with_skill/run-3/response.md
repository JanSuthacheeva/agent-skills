I reproduced SHOP-311 and found the cause. `list --tag` isn't broken, as the ticket guesses: `bm add` wipes the tags of every bookmark in the file.

**Root cause:** `toRecord()` at `src/store.ts:26` builds the saved record without `tags`. `save()` (`src/store.ts:54`) writes through it, and `add()` is the only command that calls `save()`, so every `bm add` drops all tags. `tag()` at `src/store.ts:74` saves through its own workaround, which is why tagging on its own looks fine. The bug came in with 0b70eb5, which added tags but patched `tag()` instead of `toRecord()`.

**Evidence:** I ran the CLI against a scratch file (`BM_FILE`) with the reporter's steps:
1. `add`, then `tag 1 work`: `list --tag work` shows bookmark 1, and the file holds `"tags": ["work"]`.
2. `add` a second bookmark: the file no longer has any `tags` key, and `list --tag work` prints nothing.

It fails every time.

**What else is affected:**
- Anyone who ran `bm add` after tagging has already lost those tags. They aren't stored anywhere else, so the fix can't bring them back.
- Anything else that calls `save()` in the future would drop tags the same way.

**Plan:** `docs/plans/2026-10-27-fix-tags-lost-on-add.md`. It starts with a regression test in `test/store.tags.test.ts`, then adds `tags` to `toRecord()` and changes `tag()` to save through `save()`. I worked out the failure message the new test should give from the code but didn't run it.

**Open question:**
1. What do we do about tags users have already lost? I recommend a release note telling them to re-tag affected bookmarks, since they can't be recovered.

Nothing is committed; the plan file is the only change in the working tree.