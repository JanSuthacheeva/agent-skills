I reviewed the branch and fixed four bugs where the code didn't match the plan, each with a failing test first. All 14 tests pass, and a final run of the CLI against a temp store shows the corrected behaviour. A separate agent that hadn't seen the work checked the fix commits: each fix works, its test fails without it, and nothing else broke.

**Fixed**
- **Duplicate tags:** tagging a bookmark with a tag it already had stored it twice (`["work","work"]`). It now does nothing, as planned. Commit `7665584`.
- **Wrong exit code:** `bm tag` on an unknown id exited 2; the plan and `AGENTS.md` say not found is exit 1. Commit `f63cb02`.
- **`list --tag` didn't clean up the tag:** `--tag Work` found nothing, and `--tag "to do"` exited 0 instead of printing `invalid tag`. Commit `6433e80`.
- **Wrong method name:** the store method was `listTagged` instead of the planned `listByTag`. Commit `3fccecd`.
- **Missing tests:** the plan's task 3 was ticked off claiming tests for a duplicate tag and an unknown id, but they didn't exist. They're added with the fixes above.

**Open** (I left these because they change how the commands behave for users):
- `bm list --tag` with no value, and `bm list --anything`, quietly list every bookmark and exit 0. I recommend printing `usage: bm list [--tag <tag>]` and exiting 2.
- `bm tag "" work` reads the id as `0` and reports `no bookmark 0` (exit 1) instead of the usage error. I recommend accepting only digits as an id.
- The project has no lint or type check set up, so tests are the only automated check.

**Where to look**
1. `src/store.ts`, from `load()` through `tag()` to `save()`: files saved before tags existed, and that each tag is written only once.
2. `src/cli.ts` `run()`: which errors map to which exit codes, and how `list --tag` is parsed.
3. `src/tags.ts` and the tests are routine and can be skimmed.

I added this summary to the plan as a `## Review` section (`88c5440`). Nothing is pushed.

Should I fix the two open items now, or go straight to writing the merge request?