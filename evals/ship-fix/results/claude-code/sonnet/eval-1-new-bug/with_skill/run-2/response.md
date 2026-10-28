**SHOP-311 is diagnosed and reproduced. No code has changed, and the fix plan is waiting for your approval.**

**Root cause:** `toRecord()` at `src/store.ts:25` leaves out `tags`. `add()` rewrites every existing bookmark through `save()`, which uses `toRecord()`, so each `bm add` erases all tags. `list --tag` itself is fine; it finds nothing because the tags are no longer in the file. The bug came in with 6d668ea, which added tags but didn't update `toRecord()`.

**Evidence:** I ran the reporter's steps through the real CLI with a scratch `BM_FILE`. Tagging bookmark 1 `work` made `list --tag work` show it. After `bm add` of a third bookmark, the file had no `tags` key on any bookmark and `list --tag work` printed nothing. This happens every run.

**Also affected:**
- `save()` is public and has the same flaw, so the same fix covers it.
- Files where a bookmark was added after tagging have already lost those tags. They can't be recovered from the file.

**Plan:** `docs/plans/2026-10-27-fix-add-drops-tags.md`. It has two tasks:
1. Add a regression test and fix `toRecord()`. `tag()` also switches to `save()`.
2. Re-run the reproduction.

**Open question:**
1. Should we repair already-damaged files? I recommend no, because the tags aren't in the file. The MR would tell users to re-tag instead.

Do you approve the plan and my answer to the open question? Once you do, I'll create a `SHOP-311` branch and commit the plan. Then please run `/compact` and say "continue fixing".