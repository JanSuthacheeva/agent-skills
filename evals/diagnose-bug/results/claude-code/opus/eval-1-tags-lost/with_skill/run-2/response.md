I found the cause of SHOP-311. It isn't `list --tag`, as the reporter guessed: adding a bookmark erases the tags of every existing bookmark in the file.

**Root cause:** `toRecord()` in `src/store.ts:26` doesn't include `tags` when it turns a bookmark into what gets written to the file. `add()` saves through it (`src/store.ts:53` and `src/store.ts:60`), so every `add` rewrites the whole file without tags. `tag()` only works because it adds `tags` back itself (`src/store.ts:74`). The bug came in with 0b70eb5 ("tag bookmarks and list by tag"), which added `tags` everywhere except `toRecord()`.

**Evidence:**
- **Reproduction:** I used the real CLI on a scratch file: add two bookmarks, tag both `work`, run `list --tag work`. Both bookmarks are listed. After `add https://c.example C`, `list --tag work` prints nothing, and no record in the file has a `tags` key any more. It fails every time.
- **Experiment:** I called the store directly in a throwaway script. After tagging, a bookmark's tags were `["work"]`; after saving and reloading, they were `[]`.
- **Tests:** all 15 pass, because none of them adds a bookmark after tagging.

**Also affected:** Anyone who added a bookmark after tagging has already lost those tags from their file. There's no other copy, so the fix can't bring them back. Nothing else writes the file, so there are no other places with the same bug.

**Plan:** `docs/plans/2026-10-27-fix-tags-lost-on-add.md`. It starts with a regression test that fails today, then makes `toRecord()` save `tags` and has `tag()` save the normal way instead of patching. The last task re-runs the reproduction.

**Open question:**
1. Should we tell users that tags may have been lost and need to be re-applied? I recommend yes: say so on SHOP-311 and in the release note.

I didn't change any code or commit anything; the plan file is the only change in the working tree.