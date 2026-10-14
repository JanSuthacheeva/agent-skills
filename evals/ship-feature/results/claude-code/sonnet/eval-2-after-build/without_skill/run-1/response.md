The bookmark tags feature is now finished and committed. Tests pass (15), and I ran `add`, `tag` and `list --tag` against a temp store file. The output and exit codes match the plan.

All plan tasks were already checked off, but the code didn't match the plan. I fixed these:
- **Duplicate tags:** tagging the same tag twice stored it twice. It's now a no-op.
- **Exit code:** an unknown id exited 2. It now exits 1 with `no bookmark <id>`.
- **Name:** `listTagged` is now `listByTag`, as the plan says.
- **Normalization:** `list --tag` didn't normalize its argument. `list --tag " Work "` now finds `work`, and `list --tag "to do"` fails with exit 2.
- **Tests:** I added the ones the plan called for and that were missing: duplicate tag, unknown id, non-numeric id, and `list --tag` normalization.

I made the fixes in one commit on `feature/bookmark-tags`: "bm: make tagging idempotent and match the plan's errors".

I haven't run the `review-changes` skill or opened a merge request. Do you want either?