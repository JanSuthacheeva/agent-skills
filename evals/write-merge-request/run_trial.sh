#!/usr/bin/env bash
# Run one write-merge-request eval trial headlessly with `claude -p`.
# Usage: run_trial.sh <eval-name> <prompt> <config> <run-dir> <fixture-root>
#   config: with_skill | without_skill. Runs are isolated from user and
#   plugin settings; with_skill copies the skill into the fixture's project
#   skills, so its presence is the only difference. without_skill gets the
#   title rule as a system prompt line, so it is judged on the rest.
#   FLOW=stub (default) gives the trial a flow id and the fixture's logging
#   flow stub; FLOW=absent leaves it no flow command and no flow id.
set -euo pipefail
name=$1; prompt=$2; cfg=$3; run=$4; fixtures=$5
here=$(cd "$(dirname "$0")" && pwd)
fx="$fixtures/$(echo "$run" | tr / _)"
"$here/setup_fixture.sh" "$name" "$fx" >/dev/null
mkdir -p "$run/outputs"
ln -sfn "$fx/repo" "$run/repo"; ln -sfn "$fx/origin.git" "$run/origin.git"
cp "$fx/base_sha" "$run/base_sha"; ln -sfn "$fx/calls.jsonl" "$run/calls.jsonl"
if [ "$cfg" = with_skill ]; then
  mkdir -p "$fx/repo/.claude/skills"
  cp -R "$here/../../skills/write-merge-request" "$fx/repo/.claude/skills/"
  echo ".claude/" >> "$fx/repo/.git/info/exclude"
fi
case ${FLOW:-stub} in
  stub) export FLOW_ID=eval-trial ;;
  absent)
    rm -f "$fx/bin/flow" "$fx/flow.log"; unset FLOW_ID
    PATH=$(IFS=:; for d in $PATH; do [ -x "$d/flow" ] || printf '%s:' "$d"; done); PATH=${PATH%:} ;;
  *) echo "FLOW must be stub or absent" >&2; exit 1 ;;
esac
args=(-p "$prompt" --output-format json --model "${MODEL:-claude-opus-5-5}" --effort "${EFFORT:-medium}"
      --setting-sources project,local --strict-mcp-config --mcp-config '{"mcpServers": {}}'
      --disallowedTools AskUserQuestion
      --allowedTools Skill "Bash(git *)" "Bash(clickup-axi *)" "Bash(glab *)" "Bash(gh *)" Read Glob Grep)
if [ "$cfg" = without_skill ]; then
  args+=(--append-system-prompt "MR titles: \`<ticket ID> <ticket title>\` when the branch name has a ticket ID and clickup-axi can read the ticket, otherwise Scoped Commits (\`<scope>: <description>\`).")
fi
(cd "$fx/repo" && PATH="$fx/bin:$PATH" claude "${args[@]}" < /dev/null) > "$run/outputs/raw.json" 2> "$run/outputs/stderr.txt" || true
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
