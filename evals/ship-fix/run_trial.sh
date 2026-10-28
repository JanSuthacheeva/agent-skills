#!/usr/bin/env bash
# Run one ship-fix eval trial headlessly with `claude -p`.
# Usage: run_trial.sh <eval-name> <prompt> <config> <run-dir> <fixture-root>
#   config: with_skill | without_skill. Both configs get the four fix flow
#   skills in the fixture's project skills; with_skill adds ship-fix.
#   Runs are isolated from user and plugin settings, and BM_FILE points
#   into the fixture, so no run touches a real bookmarks file.
set -euo pipefail
name=$1; prompt=$2; cfg=$3; run=$4; fixtures=$5
here=$(cd "$(dirname "$0")" && pwd)
fx="$fixtures/$(echo "$run" | tr / _)"
"$here/setup_fixture.sh" "$name" "$fx"
mkdir -p "$run/outputs" "$fx/repo/.claude/skills"
ln -sfn "$fx" "$run/fixture"; cp "$fx/base_sha" "$fx/branch_sha" "$run/"
skills="diagnose-bug implement-plan review-changes write-merge-request commit"
[ "$cfg" = with_skill ] && skills="$skills ship-fix"
for s in $skills; do cp -R "$here/../../skills/$s" "$fx/repo/.claude/skills/"; done
echo ".claude/" >> "$fx/repo/.git/info/exclude"
args=(-p "$prompt" --output-format json --model "${MODEL:-claude-sonnet-5-5}" --effort "${EFFORT:-medium}"
      --setting-sources project,local --strict-mcp-config --mcp-config '{"mcpServers": {}}'
      --disallowedTools AskUserQuestion --permission-mode acceptEdits
      --settings '{"permissions": {"deny": ["Bash(git push:*)"]}}'
      --allowedTools Skill Bash Read Edit Write Glob Grep Agent)
(cd "$fx/repo" && PATH="$fx/bin:$PATH" BM_FILE="$fx/user-bookmarks.json" claude "${args[@]}" < /dev/null) > "$run/outputs/raw.json" 2> "$run/outputs/stderr.txt" || true
python3 - "$run" <<'P'
import json, sys, pathlib
run = pathlib.Path(sys.argv[1])
d = json.loads((run / "outputs/raw.json").read_text() or "{}")
(run / "outputs/response.md").write_text(d.get("result", ""))
u = d.get("usage", {})
tok = sum(u.get(k, 0) for k in ("input_tokens", "output_tokens", "cache_creation_input_tokens"))
ms = d.get("duration_ms", 0)
(run / "timing.json").write_text(json.dumps({
    "total_tokens": tok, "output_tokens": u.get("output_tokens", 0),
    "cache_read_tokens": u.get("cache_read_input_tokens", 0),
    "cost_usd": d.get("total_cost_usd", 0), "num_turns": d.get("num_turns", 0),
    "duration_ms": ms, "total_duration_seconds": round(ms / 1000, 1),
    "session_id": d.get("session_id", "")}))
P
"$here/../shared/session_usage.py" "$run"
