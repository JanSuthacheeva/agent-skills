#!/usr/bin/env bash
# Build a throwaway repo for one review-changes eval: the bookmarks app
# from the implement-plan fixture on main, pushed to a local origin whose
# HEAD is main, and a branch with planted defects (see evals.json):
# - tags plan: behaviour defects (fixture/branch) or architecture defects
#   on top of correct behaviour (fixture/arch);
# - sharing plan: security defects (fixture/share) or none
#   (fixture/share-clean);
# - stacked: a remove branch (fixture/remove) on top of the pushed,
#   defective sharing branch, reviewed against that branch.
# Usage: setup_fixture.sh <eval-name> <dest-dir>
set -euo pipefail
name=$1; dest=$2
here=$(cd "$(dirname "$0")" && pwd)
app="$here/../implement-plan/fixture"
case $name in
  seeded-defects|vague-prompt) variant=branch ;;
  architecture) variant=arch ;;
  security-diff|no-origin-head) variant=share ;;
  clean-branch) variant=share-clean ;;
  stacked-base) variant=stacked ;;
  *) echo "unknown eval $name" >&2; exit 1 ;;
esac
rm -rf "$dest"; mkdir -p "$dest/repo"
cp -R "$app/common/." "$app/json/." "$dest/repo/"
cd "$dest/repo"
git init -q -b main
git config user.name "Eval User"; git config user.email "eval@example.com"
git config commit.gpgsign false
git add -A; git commit -q -m "bm: add and list bookmarks"

tick() { python3 - "$plan" "$1" <<'PY'
import re, sys
path, n = sys.argv[1], int(sys.argv[2])
lines = open(path).read().split("\n")
boxes = [i for i, l in enumerate(lines) if l.startswith("- [ ]") or l.startswith("- [x]")]
lines[boxes[n - 1]] = lines[boxes[n - 1]].replace("- [ ]", "- [x]", 1)
open(path, "w").write("\n".join(lines))
PY
}

share() {  # share <variant dir>: the sharing plan, one commit per task
  local v="$here/fixture/$1"
  plan=docs/plans/2026-11-20-bookmark-share.md
  mkdir -p docs/plans; cp "$here/fixture/plans/bookmark-share.md" "$plan"
  git add -A; git commit -q -m "docs: plan bookmark sharing"
  git rev-parse HEAD > "$dest/base_sha"
  git checkout -q -b feature/bookmark-share
  cp "$v/src/urls.ts" src/; cp "$v/test/urls.test.ts" test/; tick 1
  git add -A; git commit -q -m "bm: accept only web urls"
  cp "$v/src/opener.ts" src/; [ -f "$v/test/opener.test.ts" ] && cp "$v/test/opener.test.ts" test/; tick 2
  git add -A; git commit -q -m "bm: open urls in the browser"
  cp "$here/fixture/share/src/store.ts" src/; cp "$here/fixture/share/test/store.share.test.ts" test/; tick 3
  git add -A; git commit -q -m "bm: get and import bookmarks in the store"
  cp "$here/fixture/share/src/cli.ts" src/; cp "$here/fixture/share/test/cli.share.test.ts" test/; tick 4
  git add -A; git commit -q -m "bm: add import and open commands"
}

git init -q --bare "$dest/origin.git"
git remote add origin "$dest/origin.git"
git push -q origin main
git remote set-head origin main

case $variant in
  share|share-clean)
    share "$variant"
    [ "$name" = no-origin-head ] && git remote set-head origin -d
    git rev-parse HEAD > "$dest/branch_sha"
    exit 0 ;;
  stacked)
    share share
    git push -q origin feature/bookmark-share
    git rev-parse HEAD > "$dest/lower_sha"
    git checkout -q -b feature/bookmark-remove
    plan=docs/plans/2026-11-24-bookmark-remove.md
    cp "$here/fixture/plans/bookmark-remove.md" "$plan"
    git add -A; git commit -q -m "docs: plan removing bookmarks"
    cp "$here/fixture/remove/src/store.ts" src/; tick 1
    git add -A; git commit -q -m "bm: remove bookmarks in the store"
    cp "$here/fixture/remove/src/cli.ts" src/; cp "$here/fixture/remove/test/remove.test.ts" test/; tick 2
    git add -A; git commit -q -m "bm: add remove command"
    git rev-parse HEAD > "$dest/branch_sha"
    exit 0 ;;
esac

plan=docs/plans/2026-10-14-bookmark-tags.md
mkdir -p docs/plans; cp "$app/plan.md" "$plan"
git add -A; git commit -q -m "docs: plan bookmark tags"
git rev-parse HEAD > "$dest/base_sha"

git checkout -q -b feature/bookmark-tags
b="$here/fixture/branch"
cp "$b/src/tags.ts" src/; cp "$b/test/tags.test.ts" test/; tick 1
git add -A; git commit -q -m "bm: normalize tags"
cp "$b/src/bookmark.ts" "$b/src/store.ts" src/; cp "$b/test/store.tags.test.ts" test/; tick 2; tick 3
git add -A; git commit -q -m "bm: tag bookmarks in the store"
cp "$b/src/cli.ts" src/; cp "$b/test/cli.tags.test.ts" test/; tick 4; tick 5
git add -A; git commit -q -m "bm: add tag command and list --tag"
if [ "$variant" = arch ]; then
  # Same history, but the last commit carries the architecture defects.
  cp "$here/fixture/arch/src/store.ts" "$here/fixture/arch/src/cli.ts" src/
  cp "$here/fixture/arch/test/"*.ts test/
  git add -A; git commit -q --amend --no-edit
fi
git rev-parse HEAD > "$dest/branch_sha"
