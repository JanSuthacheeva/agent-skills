The review is done, and I've checked the result in the repository. It added commits 18abd8f (fixes) and 9e2868c (the plan's `## Review` section), and the suite passes 14 of 14. Three items are open, so this is a stop: they need your decision before I go on.

**Fixed by the review:** four deviations from the plan, each shown by a failing test first.
- An unknown id in `bm tag` exited 2 instead of 1.
- Tagging a bookmark with a tag it already had added a duplicate instead of doing nothing.
- `list --tag Work` matched nothing because the tag wasn't normalized.
- `listTagged` is renamed to `listByTag`.

The review's own re-read was the only check on those fixes. No fresh agent looked at them.

**Open items, with the reviewer's recommendations:**
1. **`bm list --tag` with no value** silently lists every bookmark. I recommend a usage error with exit 2.
2. **`bm tag "" x`** reads the empty id as 0 and prints `no bookmark 0`. I recommend rejecting empty ids with the usage message and exit 2.
3. **A corrupt store file** makes `load()` throw a raw `SyntaxError`. This predates the branch. I recommend deferring it as a separate change, since it isn't part of tags.

My recommendation is to build 1 and 2, which are small and tag-specific, and to leave 3 out. I would add 1 and 2 as new tasks under `## Tasks`, build them, and have a second review cover those commits.

Which of these should I build?