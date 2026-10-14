I found six problems on the branch and fixed all of them in two commits. A separate agent then reviewed the fixes with no context from my work and confirmed each one. All 17 tests pass, and I ran `add`, `tag` and `list --tag` against a temporary store file and got the output the plan describes.

## Fixed

- **Duplicate tags were saved:** running `bm tag 1 work` and then `bm tag 1 Work` stored `["work","work"]`. The plan says a repeated tag does nothing. - `1d904a6`
- **Tag search ignored case:** `bm list --tag Work` printed nothing, because the search didn't normalize the tag. The method was also called `listTagged` instead of the plan's `listByTag`; it is renamed now. - `1d904a6`
- **Wrong exit code for an unknown id:** `bm tag 9 work` exited with 2. The plan and AGENTS.md both say 1. - `d45995d`
- **Empty or blank id:** `bm tag "" work` was read as id 0 and printed `no bookmark 0`, when it should print the usage line and exit 2. Values like `0x1` were also accepted as ids. Now only plain digits are. - `d45995d`
- **`bm list --tag` with no tag:** it silently listed every bookmark. It now prints `usage: bm list [--tag <tag>]` and exits 2. The plan doesn't specify this case, but it is new on this branch, so changing it was cheap. - `d45995d`
- **Missing tests:** there were no tests for a duplicate tag, an unknown id or a bad id, though the plan's task list asks for them. They are added with the fixes above.

## Open

- **No type checking:** the project has no `tsc` setup, so types are never checked. I recommend adding a strict `tsc --noEmit` script.
- **Extra arguments to `list`:** anything after `list` other than `--tag` is ignored and the full list is printed. That was already the case before this branch and the plan doesn't cover it, so I left it.
- **Commit method:** your instructions say to commit with the `/commit` skill, but it isn't installed here, so I committed with plain `git` in the existing message style.

Nothing has been pushed.

## Where to look

1. `src/store.ts`, `tag()` and `load()`: this is the only code that writes the stored file, and it fills in an empty tag list for bookmarks saved before this change.
2. `src/cli.ts`, `run()`: how errors become messages and exit codes.

The rest is routine and can be skimmed: `src/tags.ts`, the `Bookmark` type change, and the tests.