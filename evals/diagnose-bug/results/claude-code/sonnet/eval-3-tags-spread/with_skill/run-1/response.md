Diagnosis of SHOP-313 is finished and the plan is written. I changed no code.

**Root cause:** `src/store.ts:21` defines a single module-level `noTags` array. `fromRecord` (`src/store.ts:33`) assigns it as `tags` to every record that has no `tags` key. All of those bookmarks therefore share one array, and `tag()` pushes into it. Every such bookmark gets the tag, and `save` writes it into each record. The reporter's guess that the id is ignored is wrong. It came in with commit 72964d7.

**Evidence:**
- **Reproduction:** I used a bookmarks file written before tags existed, with no `tags` key on its records. After `bm tag 3 recipes`, `bm list --tag recipes` listed bookmarks 1, 2 and 3.
- **Control:** a file built entirely with the current `bm` listed only the tagged bookmark.

**Also affected:** Any pre-tags file where `bm tag` has been run now has that tag on all of its untagged bookmarks. The fix won't undo that, because there's no way to tell which tags were intended.

**Plan:** `docs/plans/2026-10-27-fix-tag-applies-to-all-bookmarks.md`. The fix is to use `record.tags ?? []` and delete `noTags`. The plan adds a regression test first. The working tree is otherwise untouched.

**Open question:**
1. Should already-damaged files be repaired? I recommend no, since intent can't be recovered. Mention it in release notes, and consider an `untag` command if people ask for one.