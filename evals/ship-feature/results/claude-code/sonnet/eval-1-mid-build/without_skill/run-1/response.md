Bookmark tags are built: all five plan tasks are done and committed, and the full suite passes (18 tests). The repo has no lint or type-check script, so I ran neither. Nothing is pushed.

**Commits**
- `550c919` normalize tags (already done when I started)
- `c764eb8` store tags on bookmarks. Files written before tags existed load with `tags: []`.
- `f25ceff` `BookmarkStore.tag` and `listByTag`, plus `BookmarkNotFoundError`
- `73b938f` `bm tag <id> <tag>` and `bm list --tag <tag>`
- `1788c4f` plan checklist ticked

**End-to-end check** against a temp `BM_FILE`:
- `add` twice, then `tag 2 " Work "` printed `tagged 2 work`.
- `list --tag work` printed only `2  Deno  https://deno.com`.
- `tag 2 "to do"` printed `invalid tag: to do` and exited 2.
- `tag 9 x` printed `no bookmark 9` and exited 1.
- `tag abc x` printed `usage: bm tag <id> <tag>` and exited 2.
- The store file holds `tags` on every bookmark.

**Deviations from the plan**
- `list` rejects malformed `--tag` usage (a missing value or extra arguments) with `usage: bm list [--tag <tag>]` and exit 2. The plan didn't specify this.
- The id check is a strict digits-only test, so `bm tag "" x` and `bm tag 1.5 x` are usage errors rather than an unknown id.
- `run` is now a thin wrapper that maps `InvalidTagError` to exit 2 and `BookmarkNotFoundError` to exit 1. The command logic moved into a `dispatch` function in the same file.

**How it works:** `main` calls `run`, which calls `dispatch`. `dispatch` normalizes the tag with `normalizeTag`, then calls `BookmarkStore.tag` or `listByTag`. Those load the file, change or filter it, and save it. Tagging a bookmark with a tag it already has does nothing. Nothing is blocked or left open.