The bookmark tags feature is built and committed on `feature/bookmark-tags`, but I haven't reviewed the branch or opened a merge request. All 16 tests pass, and an end-to-end run against a temp store gave the expected output and exit codes.

The earlier commits had four gaps against the plan, which I fixed in one commit (`8e30201`):
- **Unknown id:** `bm tag 9 x` exited 2. It now exits 1, as the plan says.
- **Duplicate tags:** tagging a bookmark with a tag it already has added the tag twice. It is now a no-op.
- **Case in the filter:** `list --tag WORK` found nothing because the filter wasn't normalized. It now matches.
- **Name:** `listTagged` is now `listByTag`.

The existing tests passed despite all four, so I added tests for the duplicate tag, the unknown id, a non-numeric id and the uppercase filter.

**Mistake to know about:** I ran `bm add` without setting `BM_FILE`, so it wrote a stray bookmark (id 2, `https://a.com`) into your real `~/.bookmarks.json`. I removed that entry and left your existing bookmark 1 untouched. I only re-saved the file through Node with two-space indentation, so its formatting may differ slightly from before.

Next I'd run `/review-changes` on the branch, then `/write-merge-request`. Say if you want me to go ahead with those.