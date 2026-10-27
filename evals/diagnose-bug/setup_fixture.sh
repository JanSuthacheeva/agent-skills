#!/usr/bin/env bash
# Build a throwaway repo for one diagnose-bug eval: the bm bookmarks app on
# main, whose tags commit left BookmarkStore.save() writing through a
# toRecord() that predates tags, so every `bm add` drops all tags (SHOP-311).
# The suite is green and misses it. SHOP-312 (quotes in titles) does not
# reproduce. bin/ holds the forge and ticket stubs, logging to calls.jsonl.
# Usage: setup_fixture.sh <eval-name> <dest-dir>
set -euo pipefail
name=$1; dest=$2
here=$(cd "$(dirname "$0")" && pwd)
case $name in
  tags-lost|not-reproducible) ;;
  *) echo "unknown eval $name" >&2; exit 1 ;;
esac
. "$here/../shared/forge_stubs.sh"

rm -rf "$dest"; mkdir -p "$dest/repo"
forge_stubs "$dest" "$here/tickets.json"
cd "$dest/repo"
git init -q -b main
git config user.name "Eval User"; git config user.email "eval@example.com"
git config commit.gpgsign false
c() { git add -A; git commit -q "$@"; }

cp -R "$here/fixture/base/." .
c -m "bm: add and list bookmarks"
cat > README.md <<'P'
# bm

Bookmarks on the command line.

    bm add <url> [title]
    bm list
P
c -m "docs: add readme"
cp -R "$here/fixture/tags/." .
cat >> README.md <<'P'
    bm tag <id> <tag>
    bm list --tag <tag>
P
c -m "bm: tag bookmarks and list by tag"
git rev-parse HEAD > "$dest/base_sha"
