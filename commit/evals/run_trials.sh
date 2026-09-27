#!/usr/bin/env bash
# Run one commit-skill eval trial headlessly with `claude -p`.
# Usage: run_trials.sh <eval-name> <prompt> <config> <run-dir> <fixture-root>
#   config: with_skill | without_skill. Both run in the user's normal
#   environment; for without_skill, hide the commit skill beforehand
#   (see run_iteration.sh) so only its presence differs.
set -euo pipefail
name=$1; prompt=$2; cfg=$3; run=$4; fixtures=$5
here=$(cd "$(dirname "$0")" && pwd)
fx="$fixtures/$(echo "$run" | tr / _)"
"$here/setup_fixture.sh" "$name" "$fx" >/dev/null
mkdir -p "$run/outputs"
ln -sfn "$fx/repo" "$run/repo"; ln -sfn "$fx/origin.git" "$run/origin.git"; cp "$fx/base_sha" "$run/base_sha"
args=(-p "$prompt" --output-format json --model "${MODEL:-claude-opus-5-5}"
      --allowedTools Skill "Bash(git *)" "Bash(git:*)" Read Glob Grep)
if [ "$cfg" = without_skill ]; then
  args+=(--append-system-prompt \
    "Write commit messages in Scoped Commits format: \`<scope>: <description>\`.")
fi
(cd "$fx/repo" && claude "${args[@]}" < /dev/null) > "$run/outputs/raw.json" 2> "$run/outputs/stderr.txt" || true
python3 - "$run" <<'P'
import json, sys, pathlib
run = pathlib.Path(sys.argv[1])
d = json.loads((run / "outputs/raw.json").read_text())
(run / "outputs/response.md").write_text(d.get("result", ""))
u = d.get("usage", {})
# total_tokens excludes cache reads: they are dominated by the shared system
# prompt and would drown out what the skill itself costs.
tok = sum(u.get(k, 0) for k in ("input_tokens", "output_tokens", "cache_creation_input_tokens"))
ms = d.get("duration_ms", 0)
(run / "timing.json").write_text(json.dumps({
    "total_tokens": tok, "output_tokens": u.get("output_tokens", 0),
    "cache_read_tokens": u.get("cache_read_input_tokens", 0),
    "cost_usd": d.get("total_cost_usd", 0), "num_turns": d.get("num_turns", 0),
    "duration_ms": ms, "total_duration_seconds": round(ms / 1000, 1)}))
P
