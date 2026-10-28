#!/usr/bin/env bash
# Run one diagnose-bug eval trial headlessly with `claude -p`.
# Usage: run_trial.sh <eval-name> <prompt> <config> <run-dir> <fixture-root>
#   config: with_skill | systematic_debugging | without_skill. Runs are
#   isolated from user and plugin settings and get the same prompt.
#   with_skill copies diagnose-bug into the fixture's project skills,
#   systematic_debugging copies superpowers' systematic-debugging there
#   instead, so the skill is the only difference. BM_FILE points into the
#   fixture, so no run touches a real bookmarks file.
set -euo pipefail
name=$1; prompt=$2; cfg=$3; run=$4; fixtures=$5
here=$(cd "$(dirname "$0")" && pwd)
debugging=${SYSTEMATIC_DEBUGGING:-$HOME/.claude/plugins/cache/claude-plugins-official/superpowers/7.0.0/skills/systematic-debugging}
fx="$fixtures/$(echo "$run" | tr / _)"
"$here/setup_fixture.sh" "$name" "$fx" >/dev/null
mkdir -p "$run/outputs"
ln -sfn "$fx" "$run/fixture"; cp "$fx/base_sha" "$run/"
case $cfg in
  with_skill) skill="$here/../../skills/diagnose-bug" ;;
  systematic_debugging) skill=$debugging ;;
  without_skill) skill= ;;
  *) echo "unknown config $cfg" >&2; exit 1 ;;
esac
if [ -n "$skill" ]; then
  mkdir -p "$fx/repo/.claude/skills"
  cp -R "$skill" "$fx/repo/.claude/skills/"
  echo ".claude/" >> "$fx/repo/.git/info/exclude"
fi
args=(-p "$prompt" --output-format json --model "${MODEL:-claude-opus-5-5}" --effort "${EFFORT:-medium}"
      --setting-sources project,local --strict-mcp-config --mcp-config '{"mcpServers": {}}'
      --disallowedTools AskUserQuestion --permission-mode acceptEdits
      --settings '{"permissions": {"deny": ["Bash(git push:*)"]}}'
      --allowedTools Skill Bash Read Edit Write Glob Grep Agent)
(cd "$fx/repo" && PATH="$fx/bin:$PATH" BM_FILE="$fx/user-bookmarks.json" claude "${args[@]}" < /dev/null) \
  > "$run/outputs/raw.json" 2> "$run/outputs/stderr.txt" || true
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
