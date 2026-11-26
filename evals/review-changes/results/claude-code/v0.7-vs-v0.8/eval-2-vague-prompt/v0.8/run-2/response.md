I reviewed `feature/bookmark-tags` against `main` and its plan, and fixed three bugs. Tests pass (17 of 17), and I didn't push anything.

**Fixed**
- **Repeated tags were saved twice.** Running `bm tag 1 work` twice wrote `"tags": ["work", "work"]` to the file. The plan says this should do nothing, and now it does: it doesn't save the file either. (6a222de)
- **`bm list --tag Work` printed nothing.** Tags are stored in lowercase, but the filter compared the tag exactly as typed. The CLI and the store both normalize it now, and `listTagged` is renamed to `listByTag` to match the plan. (6a222de)
- **Unknown id gave the wrong exit code.** `bm tag 9 work` exited with 2, but `AGENTS.md` and the plan say "not found" is 1. (c73caae)

I wrote a failing test for each fix first. I also added the tests the plan asked for but the branch didn't have: a repeated tag, an unknown id, a non-numeric id, and an invalid tag in `list --tag`.

**Open**
- `bm list --tag` with no tag after it quietly lists every bookmark. I'd make it print the usage message and exit 2, but I left it alone because it's user-visible behaviour the plan doesn't cover.

**Where to look**
1. `tag()` in `src/store.ts`: it's the only new code that writes to the file.
2. `run()` in `src/cli.ts`: how errors become exit codes, and how `list --tag` reads its argument.

You can skim the rest of the branch.

**Checks**
- **Tests:** they last passed at c73caae. The project has no lint or type check to run.
- **Security:** `/security-review` found nothing.
- **Fix review:** a separate agent checked my fix commits and found no problems.

I added this summary to the end of the plan as a `## Review` section (642b6de).