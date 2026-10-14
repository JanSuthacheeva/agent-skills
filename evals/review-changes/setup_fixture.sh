#!/usr/bin/env bash
# Build a throwaway repo for one review-changes eval: the bookmarks app and
# tags plan from the implement-plan fixture on main, and a branch that
# implements the plan with planted defects (see evals.json): plan and
# behaviour defects (fixture/branch) or architecture defects on top of
# correct behaviour (fixture/arch).
# Usage: setup_fixture.sh <eval-name> <dest-dir>
set -euo pipefail
name=$1; dest=$2
here=$(cd "$(dirname "$0")" && pwd)
app="$here/../implement-plan/fixture"
case $name in
  seeded-defects|vague-prompt) variant=branch ;;
  architecture) variant=arch ;;
  *) echo "unknown eval $name" >&2; exit 1 ;;
esac
rm -rf "$dest"; mkdir -p "$dest/repo"
cp -R "$app/common/." "$app/json/." "$dest/repo/"
cd "$dest/repo"
git init -q -b main
git config user.name "Eval User"; git config user.email "eval@example.com"
git config commit.gpgsign false
plan=docs/plans/2026-10-14-bookmark-tags.md
git add -A; git commit -q -m "bm: add and list bookmarks"
mkdir -p docs/plans; cp "$app/plan.md" "$plan"
git add -A; git commit -q -m "docs: plan bookmark tags"
git rev-parse HEAD > "$dest/base_sha"

git checkout -q -b feature/bookmark-tags
tick() { python3 - "$plan" "$1" <<'PY'
import re, sys
path, n = sys.argv[1], int(sys.argv[2])
lines = open(path).read().split("\n")
boxes = [i for i, l in enumerate(lines) if l.startswith("- [ ]") or l.startswith("- [x]")]
lines[boxes[n - 1]] = lines[boxes[n - 1]].replace("- [ ]", "- [x]", 1)
open(path, "w").write("\n".join(lines))
PY
}
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
