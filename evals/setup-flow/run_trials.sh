#!/usr/bin/env bash
# Run one setup-flow eval trial headlessly with `claude -p`, then grade it.
# Usage: run_trials.sh <eval-name> <prompt> <config> <run-dir> <fixture-root>
#   config: with_skill | without_skill. Runs are isolated from user and
#   plugin settings; with_skill copies the skill into the fixture's project
#   skills, so its presence is the only difference. Trials run one at a time:
#   their dry runs would fight over the same ports.
set -euo pipefail
name=$1; prompt=$2; cfg=$3; run=$4; fixtures=$5
here=$(cd "$(dirname "$0")" && pwd)
fx="$fixtures/$(echo "$run" | tr / _)"
"$here/setup_fixture.sh" "$name" "$fx" >/dev/null
mkdir -p "$run/outputs"
ln -sfn "$fx/shop" "$run/repo"; cp "$fx/base_sha" "$run/base_sha"
if [ "$cfg" = with_skill ]; then
  mkdir -p "$fx/shop/.claude/skills"
  cp -R "$here/../../skills/setup-flow" "$fx/shop/.claude/skills/"
  echo ".claude/" >> "$fx/shop/.git/info/exclude"
fi
args=(-p "$prompt" --output-format json --model "${MODEL:-claude-opus-5-5}" --effort "${EFFORT:-medium}"
      --setting-sources project,local --strict-mcp-config --mcp-config '{"mcpServers": {}}'
      --allowedTools Skill Bash Read Write Edit Glob Grep)
args+=(--append-system-prompt \
  "flow runs .flow/setup and .flow/teardown in each worker's git worktree (.flow/worktrees/<name>) with FLOW_SLOT (1-20), FLOW_WORKTREE, FLOW_REPO, FLOW_NAME and FLOW_ID set.")
(cd "$fx/shop" && claude "${args[@]}" < /dev/null) > "$run/outputs/raw.json" 2> "$run/outputs/stderr.txt" || true
python3 - "$run" <<'P'
import json, sys, pathlib
run = pathlib.Path(sys.argv[1])
try:
    d = json.loads((run / "outputs/raw.json").read_text())
except Exception:
    d = {}
(run / "outputs/response.md").write_text(d.get("result", ""))
u = d.get("usage", {})
tok = sum(u.get(k, 0) for k in ("input_tokens", "output_tokens", "cache_creation_input_tokens"))
ms = d.get("duration_ms", 0)
(run / "timing.json").write_text(json.dumps({
    "total_tokens": tok, "output_tokens": u.get("output_tokens", 0),
    "cost_usd": d.get("total_cost_usd", 0), "num_turns": d.get("num_turns", 0),
    "duration_ms": ms, "total_duration_seconds": round(ms / 1000, 1)}))
P
python3 "$here/grade.py" "$run" "$name"
