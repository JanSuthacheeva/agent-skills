#!/usr/bin/env bash
# Build a throwaway repo for one ship-fix eval from the diagnose-bug
# fixture (the SHOP-311 lost-tags bug), with the GitLab-style remote of the
# shared forge stubs.
#   new-bug:       main only; the flow must diagnose and stop for approval.
#   approved-plan: the approved fix plan committed on fix/SHOP-311-tags-lost;
#                  the flow must build, review and draft the MR.
# Usage: setup_fixture.sh <eval-name> <dest-dir>
set -euo pipefail
name=$1; dest=$2
here=$(cd "$(dirname "$0")" && pwd)
case $name in new-bug|approved-plan) ;; *) echo "unknown eval $name" >&2; exit 1 ;; esac
. "$here/../shared/forge_stubs.sh"
"$here/../diagnose-bug/setup_fixture.sh" tags-lost "$dest" >/dev/null
cd "$dest/repo"
forge_remote "$dest"
git push -q origin main
git update-ref refs/remotes/origin/main main
git symbolic-ref refs/remotes/origin/HEAD refs/remotes/origin/main
if [ "$name" = approved-plan ]; then
  git checkout -q -b fix/SHOP-311-tags-lost
  mkdir -p docs/plans
  cp "$here/fixture/plan.md" docs/plans/2026-10-27-fix-tags-lost.md
  git add -A; git commit -q -m "docs: plan the SHOP-311 fix" -m "Refs: SHOP-311"
fi
git rev-parse HEAD > "$dest/branch_sha"
