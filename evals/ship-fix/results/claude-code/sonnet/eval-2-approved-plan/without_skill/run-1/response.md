SHOP-311 is fixed. All 17 tests pass and the reproduction from the plan now gives the expected output. The repo has no lint or type-check script, so I ran only the tests.

**Commits**
- `783fce3` store: keep tags when saving bookmarks. `toRecord()` in `src/store.ts` now copies `tags`. The new test "adding a bookmark keeps existing tags" failed first with `[]` instead of `['work']`.
- `d973a77` store: tag() saves through save(). `tag()` now calls `save(all)`, and I removed the private `#write` helper. `save()` writes the file itself.
- `9b5cc47` docs: ticks the end-to-end task in the plan.

**End-to-end check.** After tagging bookmark 1 `work` and adding a second bookmark, `bm list --tag work` prints `1  A  https://a.example`. Before the fix it printed nothing.

**Deviations from the plan**
- The test for task 2, "tagging two bookmarks keeps both tags", passed before the refactor because `tag()` already worked. It guards the refactor and did not fail first.
- I removed `#write`. The plan doesn't mention it, but nothing used it once `tag()` went through `save()`, and it was private, so it is cheap to undo.
- I amended the first commit to add the `Refs: SHOP-311` trailer I had left off.

**Open.** Tags already lost from users' files can't be recovered and have to be added again, as the plan says.

**How it works.** `bm add` and `bm tag` in `src/cli.ts` call `BookmarkStore.add()` and `BookmarkStore.tag()`. Both end in `save()`, which writes every bookmark through `toRecord()`. That function now includes `tags`, so rewriting the file no longer drops them. `list --tag` reads through `listTagged()`, which I did not change.