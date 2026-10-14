The review is done and left two open items for you to decide.

**Fixed by the reviewer:** `bm tag "" work` printed `no bookmark 0` and exited 1. The plan says a bad id is `usage: bm tag <id> <tag>` with exit 2, so the id is now checked as digits only. A test covers it (8b1c8a0). The fix was not reviewed independently. The reviewer re-read the one-line change.

**Open items:**
1. **Extra arguments are ignored.** `bm tag 1 work extra` and `bm list --tag work extra` both ignore `extra`. The plan doesn't say what should happen, and `add` and `list` already behave this way. I recommend leaving it.
2. **`-` and `--x` are valid tags.** That matches the plan's rule of `a-z`, `0-9` and `-`. A tag with a leading `-` is awkward to type as an argument. Tightening the rule later would change what a stored tag can be, so I recommend leaving it unless it causes problems.

**Where to look:**
- `src/store.ts`, `load()` through `tag()`. Old files without `tags` read as `[]`, and a failed read throws instead of overwriting the file.
- `src/cli.ts`, the `tag` and `list` cases and `withTagErrors`. The exit codes match the plan.
- `src/tags.ts` and the tests are routine and can be skimmed.

I also need a decision on my own deviation: `bm list --tag` with no value, or with another flag, prints `usage: bm list [--tag <tag>]` and exits 2.

Do you accept both recommendations (leave as is)? If so, I'll go on to the merge request. If you want either changed, tell me which. I'll add it as a task, build it, and have a second review cover the new commits.