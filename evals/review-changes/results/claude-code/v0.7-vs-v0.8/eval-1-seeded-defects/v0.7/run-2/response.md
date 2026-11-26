I found four places where `feature/bookmark-tags` didn't match the plan and fixed all of them. Each fix has a test that fails without it, and its own commit. The tests now pass (16 of 16) at `e4f2d60`; the project has no lint or type check set up. A separate agent re-checked the four fixes and found no problems.

## Fixed
- **Wrong exit code for an unknown id:** `bm tag 7 work` printed `no bookmark 7` but exited 2. The plan and `AGENTS.md` say 1. Fixed in `734b87a`.
- **Duplicate tags:** tagging a bookmark twice with the same tag stored it twice (`["work","work"]`). The plan says this should do nothing. Fixed in `3dde465`.
- **`list --tag` skipped tag cleanup:** `--tag " Work "` found nothing, and `--tag "to do"` printed nothing and exited 0 instead of printing `invalid tag: to do` and exiting 2. The store method was also named `listTagged` instead of the planned `listByTag`; I renamed it. Fixed in `da107a6`.
- **Loose id check:** an empty or blank id was read as id 0, so you got `no bookmark 0` instead of the usage message, and `0x1` was accepted. Fixed in `e4f2d60`.

I also ran the CLI against a temporary store file to check add, tag, a repeated tag, `list --tag`, and both error cases.

## Decisions for you
- **`bm list --tag` with no value lists every bookmark** without any warning. I'd make it print the usage message and exit 2. The plan doesn't cover this case, and users would see the change, so I left it.
- **The plan links to a missing file:** it points to `.lavish/bookmark-tags-implementation.html`, which isn't in the repo. Remove the line or add the file.

## Where to look
1. `src/cli.ts`, from `run()` into `dispatch()`: how errors become messages and exit codes, and how arguments are read for `tag` and `list --tag`.
2. `src/store.ts`, from `load()` to `tag()`: how files saved before tags existed are read, and how a tag is cleaned up and checked for duplicates before saving.
3. You can skim `src/tags.ts`, `src/bookmark.ts` and the tests.

I added this summary to the plan as a `## Review` section (commit `05c6693`). Nothing has been pushed.