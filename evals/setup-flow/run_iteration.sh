#!/usr/bin/env bash
# Run every eval in evals.json for both configs, N trials each, one at a time.
# Usage: run_iteration.sh <iteration-dir> <fixture-root> [trials=2]
# CONFIGS="with_skill ..." limits which configs run (default: both).
set -euo pipefail
mkdir -p "$1" "$2"
it=$(cd "$1" && pwd); fixtures=$(cd "$2" && pwd); trials=${3:-2}
here=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$it"
claude --version | head -1 > "$it/harness.txt"
python3 - "$here/evals.json" "$it" "${CONFIGS:-with_skill without_skill}" "$trials" "$fixtures" <<'P' |
import json, os, sys
evals, it, cfgs, trials, fx = sys.argv[1], sys.argv[2], sys.argv[3].split(), int(sys.argv[4]), sys.argv[5]
for e in json.load(open(evals))["evals"]:
    d = f"{it}/eval-{e['id']}-{e['name']}"
    os.makedirs(d, exist_ok=True)
    json.dump({"eval_id": e["id"], "eval_name": e["name"], "prompt": e["prompt"],
               "assertions": e["expectations"]}, open(f"{d}/eval_metadata.json", "w"), indent=2)
    for r in range(1, trials + 1):
        for cfg in cfgs:
            sys.stdout.write("\0".join([e["name"], e["prompt"], cfg, f"{d}/{cfg}/run-{r}", fx]) + "\0")
P
xargs -0 -n5 -P1 "$here/run_trials.sh"
