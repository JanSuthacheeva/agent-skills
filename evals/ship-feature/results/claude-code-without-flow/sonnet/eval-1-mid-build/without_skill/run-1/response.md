The bookmark tags feature is built and every task in the plan is checked off. All 17 tests pass. A manual run against a temp store file also behaved as the plan describes. Everything is committed on `feature/bookmark-tags`, and nothing is pushed.

- **Store:** `Bookmark` now has `tags`. New bookmarks start with an empty list, and files saved before tags existed load with `tags: []`, so no migration is needed. `BookmarkStore` gained `tag()` and `listByTag()`, and an unknown id throws `BookmarkNotFoundError`.
- **CLI:** `bm tag <id> <tag>` and `bm list --tag <tag>` work as specified. Tags are trimmed and lowercased. Tagging with a tag the bookmark already has does nothing.
- **Errors:** the CLI maps an unknown id to `no bookmark <id>` with exit 1. An invalid tag prints `invalid tag: <raw>` and a bad id prints the usage line, both with exit 2.
- **Extras the plan didn't list:**
  - `list --tag` with no value prints `usage: bm list [--tag <tag>]` and exits 2.
  - An id that isn't a plain number, including an empty one, gets the tag usage line.

I committed each task separately, plus a last commit that ticks the plan's checklist.