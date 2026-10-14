The review finished and I checked it in the repo rather than taking the report on trust. It found three bugs and fixed them, one commit each:

- Tagging a bookmark twice with the same tag saved the tag twice. It now does nothing, as the plan says.
- `bm tag` exited with 2 instead of 1 for an unknown id, and printed `no bookmark 0` for an empty id instead of the usage message.
- `bm list --tag Work` found nothing for a bookmark tagged `work`, because the tag wasn't normalized first.

All 16 tests pass and nothing has been pushed. Two items need your decision before the merge request:

1. **`bm list --tag` with no value** lists every bookmark and exits 0. The plan doesn't cover this case.
   - **Recommendation:** print `usage: bm list [--tag <tag>]` and exit 2, the same as the other bad-input errors.
2. **The store normalizes tags in one method but not the other.** `BookmarkStore::tag` normalizes the tag even though the CLI already did, while `listByTag` relies on the CLI having done it. Nothing is broken today, but it's inconsistent.
   - **Recommendation:** have both store methods normalize. The plan says the store owns tagging and filtering, so it shouldn't depend on callers. Normalizing twice gives the same result, so the CLI can keep its own call too.

Should I take both recommendations, change either one, or skip them? Whatever you decide goes into the plan as new tasks, then a fresh build runs and a second review covers it.