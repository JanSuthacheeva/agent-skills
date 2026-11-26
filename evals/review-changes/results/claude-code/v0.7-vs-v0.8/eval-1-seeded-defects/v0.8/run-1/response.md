I reviewed `feature/bookmark-tags` against the plan and fixed five bugs that break it, one commit each, with a test written first that failed. All 16 tests pass and nothing was pushed.

**Fixed**
- **Duplicate tags:** running `bm tag 1 work` and then `bm tag 1 Work` saved `"tags": ["work","work"]`. The plan says repeating a tag should do nothing. (`fd8478d`)
- **Wrong exit code for an unknown id:** `bm tag 9 work` exited 2, but the plan and AGENTS.md say 1 for "not found". (`d0f46ca`)
- **`list --tag` didn't clean up the tag first:** `--tag Work` found nothing, and `--tag "to do"` printed nothing with exit 0 instead of `invalid tag: to do` with exit 2. (`63dbfd6`)
- **Method name:** the store method was called `listTagged`; the plan names it `listByTag`. (`d53d369`)
- **Empty id:** `bm tag "" work` printed `no bookmark 0` instead of the usage message. Ids must now be digits only, so `bm tag 1.0 x` and `bm tag " 1" work` also get the usage message now. (`621d85a`)

**Open, for you to decide**
- `bm list --tag` with no value lists every bookmark and exits 0, and the plan doesn't say what it should do. I'd make it a usage error with exit 2.
- `bm tag` cleans up the tag twice, once in the CLI and again in the store. It's harmless, and the store's copy protects anyone else who calls it, so I left it.

**Where to look**
1. `src/store.ts`, `load()` and `tag()`: how files saved before tags existed are read, and the duplicate check.
2. `src/cli.ts`, `run()`: which error gives which exit code, and how the `tag` id is parsed.

The tests and `src/tags.ts` are routine.

**Checks**
- **Tests:** all 16 pass at `621d85a`. The project has no lint or type checker set up.
- **Security:** `/security-review` on `main...HEAD` found nothing.
- **Fix review:** a separate agent checked the five fix commits and found no problems.

The review is also written into the plan as a `## Review` section, committed as `5624eab`.