The branch had four bugs where it didn't match the plan. I fixed all four, one commit each, with a test that failed before each fix. All 16 tests pass (10 before). The CLI end to end now shows the right output and exit codes. A second agent that hadn't seen my work checked the fix commits and found no problems. The repo has no lint or type-check setup, so tests are the only automated check.

## Fixed
- **Duplicate tags were saved:** running `bm tag 1 work` twice wrote `["work", "work"]` to the store file. The plan says re-adding a tag does nothing. `ac4cfef`
- **Wrong exit code for an unknown id:** `bm tag 9 work` exited 2, but the plan and `AGENTS.md` say "not found" exits 1. `59d5ad2`
- **Method name didn't match the plan:** it was `listTagged`; the plan names it `listByTag`. `6c4641e`
- **`list --tag` skipped tag cleanup:** `list --tag Work` found nothing because tags are stored lowercase. `list --tag 'to do'` printed nothing and exited 0 instead of `invalid tag: to do` with exit 2. `b7a4723`

I also added tests the plan asked for but the branch lacked: an unknown id in the store, and a non-numeric id in the CLI. Both already passed.

## Open
- **`bm list --tag` with no value lists every bookmark** instead of failing. The plan doesn't cover this case. I'd make it a usage error with exit 2, but I didn't change it because it's user-visible behaviour.
- **Ids are parsed loosely:** they go through `Number()`, so `bm tag "" work` becomes id 0 and prints `no bookmark 0`, and `0x1` becomes id 1. Minor; I'd only accept digits.
- **The plan's review page is missing:** the plan links to `.lavish/bookmark-tags-implementation.html`, which isn't in the repo.
- **The last plan task (running the CLI by hand) was ticked off,** but its output would have shown these bugs. I've now done that run myself.

## Where to look
1. `src/store.ts`, `load()` to `tag()`: how files saved before tags existed get `tags: []`, and the duplicate check before saving. This is the only part that changes stored data.
2. `src/cli.ts`, `run()`: how errors become messages and exit codes, and the `list` option parsing.

The rest is routine and can be skimmed: `src/tags.ts`, the `Bookmark` type, and the tests.

Nothing is pushed.