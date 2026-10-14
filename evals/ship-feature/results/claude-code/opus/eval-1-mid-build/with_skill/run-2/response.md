The tag feature is built and reviewed. All 5 plan tasks are done and committed on `feature/bookmark-tags`, and all 18 tests pass. The merge request is written but not opened. It needs your OK to push.

**Build:** a fresh agent did tasks 2 to 5. It made two small changes to the plan and wrote both into it:
- Errors are turned into exit codes in one place.
- `bm list` now rejects unexpected arguments with a usage message (exit 2) instead of ignoring them.

**Review:** a second fresh agent reviewed the branch on its own. It fixed two things and left nothing open:
- `bm tag 1 to do` saved only `to`. It now prints the usage line, exits 2 and saves nothing.
- The new `bm list` argument check had no test, so it added one.

It also noted a problem that already exists on `main`: a corrupt bookmarks file makes the CLI crash with a stack trace, though no data is lost. I'd leave that for a later change.

There's no MR template in the repo and no open MR for this branch.

---

**Title:** `bm: tag bookmarks and list them by tag`

**Description:**

```
Bookmarks could only be listed all at once. They can now be tagged with
`bm tag <id> <tag>` and filtered with `bm list --tag <tag>`.

- Tags are stored on each bookmark in the existing store file. Files
  written before this change have no `tags` field and are read as
  `tags: []`, so no migration is needed. The first `tag` command rewrites
  the whole file with `tags` on every bookmark.
- `normalizeTag` is the only place that decides what a valid tag is
  (trimmed, lowercased, `a-z`, `0-9` and `-`), so the store and the CLI
  agree on it. Adding a tag a bookmark already has does nothing.
- `run` hands the command to `dispatch` and turns errors into exit codes
  in one place: invalid tag 2, unknown bookmark 1.
- `bm list` with arguments other than `--tag <tag>`, and `bm tag` with
  extra arguments, now print the usage line and exit 2. Before this,
  `list` silently ignored extra arguments.

Review:
1. `src/store.ts` from `load()` through `tag()` to `save()`: reading old
   files without tags, and the full-file rewrite on the first tag. This
   is the only change to stored data.
2. `src/cli.ts` `run()` and `dispatch()`: argument checks for `tag` and
   `list --tag`, and how errors become exit codes 1 and 2.
3. `src/tags.ts` `normalizeTag()`: what counts as a valid tag.
Skim: `src/bookmark.ts`, the tests.

A corrupt store file still crashes the CLI with a stack trace. That was
already the case on `main` and is left for a later change.
```

Should I push `feature/bookmark-tags` to origin and open the merge request against `main`?