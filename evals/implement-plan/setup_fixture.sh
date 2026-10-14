#!/usr/bin/env bash
# Build a throwaway repo for one implement-plan eval from fixture/common
# plus a store variant: json (the plan fits the code) or csv (the plan
# assumes a JSON store, so adding tags changes a public file format the
# plan never decided on). plan-needs-fix uses json with a plan that asks
# for a parameter property the project forbids.
# Usage: setup_fixture.sh <eval-name> <dest-dir>
set -euo pipefail
name=$1; dest=$2
here=$(cd "$(dirname "$0")" && pwd)
case $name in
  tags-plan) variant=json ;;
  csv-store) variant=csv ;;
  plan-needs-fix) variant=json ;;
  *) echo "unknown eval $name" >&2; exit 1 ;;
esac
rm -rf "$dest"; mkdir -p "$dest/repo"
cp -R "$here/fixture/common/." "$here/fixture/$variant/." "$dest/repo/"
cd "$dest/repo"
git init -q -b main
git config user.name "Eval User"; git config user.email "eval@example.com"
git config commit.gpgsign false
git add -A; git commit -q -m "bm: add and list bookmarks"
mkdir -p docs/plans; cp "$here/fixture/plan.md" docs/plans/2026-10-14-bookmark-tags.md
if [ "$name" = plan-needs-fix ]; then
  # The plan asks for a parameter property, which AGENTS.md rules out
  # because Node cannot strip it: a cheap deviation the build must make.
  sed -i '' -e 's/  constructor(raw: string)/  constructor(readonly raw: string)/' \
    -e 's/^- Tags are lowercased and trimmed/- `InvalidTagError` keeps the rejected input as `raw`, for the CLI message.\
- Tags are lowercased and trimmed/' docs/plans/2026-10-14-bookmark-tags.md
fi
git add -A; git commit -q -m "docs: plan bookmark tags"
git rev-parse HEAD > "$dest/base_sha"
