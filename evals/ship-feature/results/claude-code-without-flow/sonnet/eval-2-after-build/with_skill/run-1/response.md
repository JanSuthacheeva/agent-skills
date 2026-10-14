The review left one decision for you. Per the flow, I'm stopping here.

**Fixed by the review** (commit `89e142d`, each with a failing test first):
- `bm tag` on an unknown id now exits 1, as the plan says. It exited 2 before.
- Tagging with a tag the bookmark already has is now a no-op. It stored a duplicate before.
- `bm list --tag` now normalizes and validates its tag. `" Work "` used to match nothing, and an invalid tag was accepted.
- `listTagged` is renamed to `listByTag`, as the plan names it.
- I did not run lint or a type check, because the project has neither script.
- The fixes were re-read by the reviewer itself, not by an independent agent. The plan's `## Review` says so.

**Open item:** `bm list --tag` with no value silently lists every bookmark, and the plan doesn't say what it should do.
- **Recommendation:** print `usage: bm list [--tag <tag>]` and exit 2. That matches the existing "bad input is 2" rule in `AGENTS.md` and avoids a silent wrong result.
- **Alternative:** leave it as it is.

The second line under Open in the review, that `load()` throws on a corrupt file, is only a note. No data is overwritten, so it needs no action.

Should I add the usage error as a new task, build it and then review the new commits? Or should I skip it and go straight to the merge request?