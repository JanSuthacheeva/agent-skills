#!/usr/bin/env bash
# Run one review-changes eval trial headlessly with `claude -p`.
# Usage: run_trial.sh <eval-name> <prompt> <config> <run-dir> <fixture-root>
#   config: with_skill | without_skill | code_review. Every run is a fresh
#   headless session isolated from user and plugin settings, so no config
#   sees how the branch was written. with_skill copies the skill into the
#   fixture's project skills; code_review replaces the prompt with Claude
#   Code's built-in `/code-review medium --fix`.
set -euo pipefail
name=$1; prompt=$2; cfg=$3; run=$4; fixtures=$5
here=$(cd "$(dirname "$0")" && pwd)
fx="$fixtures/$(echo "$run" | tr / _)"
"$here/setup_fixture.sh" "$name" "$fx" >/dev/null
mkdir -p "$run/outputs"
ln -sfn "$fx/repo" "$run/repo"; cp "$fx/base_sha" "$fx/branch_sha" "$run/"
if [ "$cfg" = with_skill ] && [ -d "$here/../../skills/review-changes" ]; then
  mkdir -p "$fx/repo/.claude/skills"
  cp -R "$here/../../skills/review-changes" "$fx/repo/.claude/skills/"
  echo ".claude/" >> "$fx/repo/.git/info/exclude"
fi
[ "$cfg" = code_review ] && prompt="/code-review medium --fix"
args=(-p "$prompt" --output-format json --model "${MODEL:-claude-opus-5-5}" --effort "${EFFORT:-medium}"
      --setting-sources project,local --strict-mcp-config --mcp-config '{"mcpServers": {}}'
      --disallowedTools AskUserQuestion --permission-mode acceptEdits
      --settings '{"permissions": {"deny": ["Bash(git push:*)"]}}'
      --allowedTools Skill Bash Read Edit Write Glob Grep Agent)
(cd "$fx/repo" && claude "${args[@]}" < /dev/null) > "$run/outputs/raw.json" 2> "$run/outputs/stderr.txt" || true
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
    "duration_ms": ms, "total_duration_seconds": round(ms / 1000, 1)}))
P
