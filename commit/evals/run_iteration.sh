#!/usr/bin/env bash
# Run every eval in evals.json for both configs, N trials each.
# Usage: run_iteration.sh <iteration-dir> <fixture-root> [trials=5] [parallel=8]
# CONFIGS="with_skill ..." limits which configs run (default: all three).
set -euo pipefail
it=$1; fixtures=$2; trials=${3:-5}; par=${4:-8}
here=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$it"

jobs() {  # jobs <config> -> NUL-separated args for run_trials.sh
  python3 - "$here/evals.json" "$it" "$1" "$trials" "$fixtures" <<'P'
import json, os, sys
evals, it, cfg, trials, fx = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]
for e in json.load(open(evals))["evals"]:
    d = f"{it}/eval-{e['id']}-{e['name']}"
    os.makedirs(d, exist_ok=True)
    json.dump({"eval_id": e["id"], "eval_name": e["name"], "prompt": e["prompt"],
               "assertions": e["expectations"]}, open(f"{d}/eval_metadata.json", "w"), indent=2)
    for r in range(1, trials + 1):
        sys.stdout.write("\0".join([e["name"], e["prompt"], cfg, f"{d}/{cfg}/run-{r}", fx]) + "\0")
P
}

for cfg in ${CONFIGS:-with_skill skill_lite without_skill}; do jobs "$cfg"; done | xargs -0 -n5 -P"$par" "$here/run_trials.sh"
