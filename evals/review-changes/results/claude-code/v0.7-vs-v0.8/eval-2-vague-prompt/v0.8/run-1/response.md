I found five bugs on `feature/bookmark-tags` that went against the plan or `AGENTS.md`, and fixed them. All 17 tests now pass. The project has no lint or type check, and I didn't push anything.

**Fixed** (tests added for each, and I checked by running the CLI):
- **Duplicate tags were saved:** tagging bookmark 1 with `work` and then `Work` stored `["work","work"]`. The plan says repeating a tag should do nothing, and now it does. I also renamed `listTagged` to `listByTag`, the name the plan uses. (`44908b2`)
- **Wrong exit code for an unknown id:** `bm tag 9 work` exited with 2. The plan and `AGENTS.md` both say "not found" exits with 1, so it does now. (`422ce74`)
- **Empty id treated as 0:** `bm tag "" work` got through the id check and printed `no bookmark 0`. It now shows the usage message, as the plan says for a non-numeric id. (`422ce74`)
- **`list --tag` didn't normalize the tag:** `bm list --tag Work` found nothing. The tag is now lowercased and trimmed, and an invalid one like `to do` exits with 2 and `invalid tag: to do`. (`422ce74`)

**Not fixed, your call** (the plan doesn't cover either):
- `bm list --tag` with no tag after it lists every bookmark instead of complaining. I'd make it a usage error that exits with 2.
- A huge id like `99999999999999999999` is reported rounded, as `no bookmark 100000000000000000000`. It's only the message that's wrong; checking the id with `Number.isSafeInteger` would fix it.

**Where to look:**
1. `src/store.ts`, from `load()` through `tag()` to `save()`: how files from before tags existed are read, and the duplicate check.
2. `src/cli.ts`: how errors in `run()` become exit codes, and how the `tag` and `list` commands read their arguments.

`src/tags.ts` and the tests are routine and fine to skim.

**Checks:** the security review compared against `main` and found nothing. A separate agent re-checked my fixes and confirmed all five; the two open items above came from that check. I also added this summary to the plan as a `## Review` section (`71c5347`).