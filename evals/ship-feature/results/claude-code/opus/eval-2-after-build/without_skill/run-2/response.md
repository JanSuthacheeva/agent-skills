The build was already finished: all plan tasks were checked off and the tests passed. I reviewed the branch, fixed four bugs, and wrote the review into the plan. All 16 tests pass and nothing is pushed.

**Fixed** (each was reproduced through the real CLI and has a test that failed before the fix):
- Running `bm tag 1 work` twice stored `work` twice. The plan says a repeated tag should do nothing, and now it doesn't. (58af351)
- The store method was named `listTagged`; I renamed it to `listByTag`, the name the plan uses. (ae7b358)
- Tagging an unknown id exited with 2 instead of 1. Also, `bm tag "" work` reported `no bookmark 0` instead of the usage line, because the empty string converts to 0. (85da30b)
- `list --tag` didn't clean up the tag before searching. `--tag Work` found nothing, and `--tag "to do"` exited 0 with no output instead of reporting an invalid tag. (c66c613)

A separate agent re-checked these fixes through the CLI, including edge-case ids like `01`, `-1`, `0x1` and `1e0`, and found no problems.

**Open:**
- **`bm list --tag` with no value lists every bookmark without any error.** I'd make it a usage error (`usage: bm list [--tag <tag>]`, exit 2). I had written a test for that, but someone removed it from `test/cli.tags.test.ts` while I was working, so I left the behaviour as it is. Do you want that change or not?
- A very large id like `99999999999999999999` gets rounded, so the error message shows the wrong number. The exit code is still right. Low priority.
- The project has no type checker or linter set up, so only the tests were run.

That same edit also made the test for a non-numeric id cover `1.5`. I committed that change along with c66c613.

**Where to look:** `src/store.ts` `load()`, where old files without tags get an empty list; then the error-to-exit-code mapping in `run()` in `src/cli.ts`; then the `--tag` parsing in the `list` case.

The next step is the merge request, which needs a push. Should I go ahead, after you decide on `list --tag` without a value?