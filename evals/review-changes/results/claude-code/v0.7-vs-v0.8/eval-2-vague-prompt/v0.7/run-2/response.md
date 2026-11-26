I reviewed `feature/bookmark-tags` against `main` and its plan, and fixed three bugs. All tests pass (15 of 15) and a separate agent re-checked the fixes. The project has no lint or type-check script, so the tests are the only check that ran. Nothing has been pushed.

**Fixed** (each with a test that fails without the fix):
- **Same tag stored twice:** tagging a bookmark twice with the same tag saved `["work","work"]` in the file. The plan says this should do nothing, and now it does. (`7a7ab99`)
- **Wrong exit code for an unknown id:** `bm tag 9 work` exited 2. The plan and AGENTS.md say "not found" exits 1, and now it does. (`91ac649`)
- **`list --tag` didn't clean up the tag:** `bm list --tag Work` found nothing, and `bm list --tag "to do"` printed nothing and exited 0. The tag is now cleaned up the same way `bm tag` does it, and an invalid tag prints `invalid tag: ...` and exits 2. I also renamed `listTagged` to `listByTag`, the name the plan uses. (`0c7b907`)

**Open** (I didn't change these because the plan doesn't say how they should behave):
- **`--tag` with no value:** `bm list --tag` (or `--tag` not given first) quietly lists every bookmark and exits 0. I'd make it print a usage message and exit 2.
- **Empty id:** `bm tag "" work` reads the id as 0 and prints `no bookmark 0` instead of the usage message. It's minor; I'd reject empty ids with the usage message.

**Where to look:**
1. `src/store.ts`, `load()`: files saved before tags existed get an empty tag list when read. Nothing else in old files is checked.
2. `src/store.ts`, `tag()`: the only new code that writes the file.
3. `src/cli.ts`, `run()`: which error gets which message and exit code.

`src/tags.ts` and the tests are routine and can be skimmed.

I also added this summary as a `## Review` section at the end of the plan (`79f91ba`).