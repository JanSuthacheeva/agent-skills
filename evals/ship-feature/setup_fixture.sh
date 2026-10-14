#!/usr/bin/env bash
# Build a throwaway repo for one ship-feature eval from the bookmark-tags
# branch of the review-changes suite, with the GitLab-style remote and the
# logging forge stubs of the write-merge-request suite.
#   mid-build:   only task 1 is built and ticked; the flow must build on.
#   after-build: all tasks are built, with planted defects, and the plan
#                has no review yet; the flow must review, not rebuild.
# Usage: setup_fixture.sh <eval-name> <dest-dir>
set -euo pipefail
name=$1; dest=$2
here=$(cd "$(dirname "$0")" && pwd)
case $name in mid-build|after-build) ;; *) echo "unknown eval $name" >&2; exit 1 ;; esac
"$here/../write-merge-request/setup_fixture.sh" review-guide "$dest" >/dev/null
cd "$dest/repo"
[ "$name" = mid-build ] && git reset -q --hard HEAD~2
git rev-parse HEAD > "$dest/branch_sha"
