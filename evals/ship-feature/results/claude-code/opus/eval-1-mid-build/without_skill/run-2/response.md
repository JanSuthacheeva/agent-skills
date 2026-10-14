The review is finished. It fixed two problems, committed the fixes, and left three questions for you. All 19 tests pass and the working tree is clean; nothing has been pushed.

**Fixed:**
- `92f78a4`: `bm tag 1 to do` used to save the tag `to`, silently drop `do` and report success. `bm list --tag work home` ignored `home`. Both now print their usage line and exit 2, and the plan is updated to match.
- `f59222e`: the plan asked for tests of empty input and invalid characters in tags, and they were missing. They're added now.
- `a4844a0`: the plan now has a review section listing the open items and where to look.

**Decisions for you:**
1. **Tags made only of hyphens are accepted.** `bm tag 1 -` saves the tag `-`, and `bm list --tag --tag` searches for a tag literally called `--tag` instead of showing usage. I recommend requiring tags to start with a letter or digit. It's a one-line change, but it decides which tags can ever be saved, so it's best done before release. Once odd tags are in people's files, tightening the rule leaves tags the CLI no longer accepts.
2. **A broken store file crashes with a stack trace.** This already happens on `main`, and no data is lost because nothing is saved after a failed read. I'd add a proper error with a clear message and exit code, in a separate change.
3. **The plan links a review page that isn't in the repo** (`.lavish/bookmark-tags-implementation.html`). Should I remove the link, or do you have the page somewhere to add?

Should I go ahead with 1 and 2 and remove the link in 3? After that, the next step is writing the pull request description for you to approve before anything is pushed.