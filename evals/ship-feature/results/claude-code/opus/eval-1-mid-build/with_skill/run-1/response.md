I finished the build and the review. The merge request is drafted, and nothing has been pushed yet.

**Build:** tasks 2-5 of the plan are done, one commit each. All 19 tests pass. The project has no lint or type-check scripts. I also ran the real CLI against a temporary store file, and it behaved as the plan says:
- adding, tagging and `list --tag` work;
- the same tag in different case or with spaces is stored once;
- an unknown id exits 1; a bad tag or bad arguments exit 2;
- a store file written before tags existed loads fine and gets a `tags` field when first tagged.

**Two changes from the plan,** both written into the plan:
- `run()` now passes commands to a private `dispatch()`, so errors are turned into messages and exit codes in one place.
- A missing tag, or `list` with anything other than `--tag <tag>`, prints the usage line and exits 2.

**Review** (in a separate agent with no access to this conversation): it found that extra arguments were silently ignored. For example, `bm tag 1 to do` tagged bookmark 1 with "to". It fixed that and found nothing else on this branch.

It did flag an older risk that isn't from this branch: the store file is overwritten in place, so a crash during a write can leave it unreadable. I'd fix that in a separate change by writing to a temporary file and then renaming it.

**Commits:**
- **Build:** `49eaf7c`, `26dc292`, `01e78c5`, `50a6428`
- **Review:** `1547fd0` (fix), `93c3115` (review notes)

---

**Title:** `bm: tag bookmarks and list them by tag`

**Description:**

```
Bookmarks had no way to be grouped. They can now be tagged with
`bm tag <id> <tag>` and filtered with `bm list --tag <tag>`.

- Tags are stored on each bookmark in the existing store file. Files
  written before this change have no `tags` field and are read as
  `tags: []`, so no migration is needed; a file is only rewritten when
  a tag is added.
- Tags are normalized in one place, `normalizeTag`: trimmed, lowercased,
  and limited to `a-z`, `0-9` and `-`. Adding a tag a bookmark already
  has does nothing and is not an error.
- `run()` delegates to a private `dispatch()`, so the error classes map
  to messages and exit codes in one place: 1 for an unknown id, 2 for an
  invalid tag or bad arguments.

Review:
1. `src/store.ts` `load()` to `tag()`: how old files without `tags`
   are read, and that tagging the same bookmark twice saves the tag once.
2. `src/cli.ts` `run()` to `dispatch()`: the error-to-exit-code mapping
   and the argument checks for `tag` and `list`, including rejecting
   extra arguments.
Skim: `src/tags.ts`, `src/bookmark.ts` and the tests.

Left out: `save()` still writes the store file in place, so a crash
mid-write can leave it truncated. This predates the branch and is
better fixed separately with a write-to-temp-and-rename.
```

Should I push `feature/bookmark-tags` and open the merge request against `main` on gitlab.com/shop/shop?