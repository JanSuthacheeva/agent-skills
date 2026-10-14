The bookmark tags feature is built and reviewed, but I haven't pushed anything. The push needs your go-ahead.

- **Build:** all five plan tasks are done and ticked. All 18 tests pass.
- **Review:** the isolated review found one bug and fixed it. `bm tag "" work` used to say `no bookmark 0`. It now prints the usage message and exits 2, as the plan says. Nothing is left open. The reviewer could not start a separate agent, so that one-line fix was not reviewed again by someone else.
- **Merge request:** none exists yet for `feature/bookmark-tags`. The target branch is `main`. There is no MR template in the repo.

**Proposed title:** `bm: add tags to bookmarks and filter the list by tag`

**Proposed description:**

```
Bookmarks could not be grouped. They can now be tagged with `bm tag <id> <tag>` and filtered with `bm list --tag <tag>`.

- Tags are stored on each bookmark in the existing store file, so there is no migration. Files written before this change load as `tags: []`.
- Tags are lowercased and trimmed in one place, `normalizeTag`, so the store and the CLI agree on what a valid tag is.
- Tagging a bookmark with a tag it already has is a no-op, not an error.
- Invalid tags exit 2 and an unknown id exits 1, as the existing CLI does.

Review:
1. `src/store.ts` `load()` to `tag()`: old files read as `tags: []`, and a corrupt file throws instead of being saved over.
2. `src/cli.ts` `run()` and `withTagErrors`: check the mapping of errors to messages and exit codes (2 invalid tag or non-numeric id, 1 unknown bookmark).
Skim: `src/tags.ts`, `list --tag` output, the tests.
```

The repo has no ticket ID, so there is no `Refs:` line.

Should I push `feature/bookmark-tags` and open the merge request with this title and description? Tell me if you want any wording changed first.