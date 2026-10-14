The review is finished. I checked the repository: it fixed four bugs in four commits (`09ed64b`, `1b3a60e`, `4f1bc15`, `46a199e`), the tests went from 10 to 15 and all pass, and the working tree is clean.

The fixes:
- Tagging a bookmark twice stored the tag twice.
- An unknown id in `bm tag` exited 2 instead of 1.
- `bm tag "" work` read the empty id as bookmark 0 instead of printing the usage error.
- `list --tag` didn't normalize the tag, so `--tag Work` matched nothing and `--tag "to do"` was accepted.

Two review items need your decision before I open the merge request:

1. **`bm list --tag` with no value** lists every bookmark and exits 0. The plan doesn't cover this case.
   - **Recommendation:** make it a usage error, `usage: bm list [--tag <tag>]`, exit 2. This matches how the other commands handle bad input.
   - Alternative: keep the current behavior.
2. **Broken link in the plan:** it links to `.lavish/bookmark-tags-implementation.html`, which isn't in the repository.
   - **Recommendation:** remove the link. That page was only for reviewing the design, and a link that doesn't resolve in the repository is just noise.
   - Alternative: commit the page.

Should I go ahead with both recommendations? If so, I'll add them as tasks in the plan, run the build again in a fresh agent and do a second review of the new commits.