#!/usr/bin/env bash
# Run every scenario in evals.json for every config, N runs each.
# Usage: run_iteration.sh <iteration-dir> [runs=1] [parallel=4]
# CONFIGS="code-design plain" limits which configs run (default: all).
# Runs that already have a timing.json are skipped, so an iteration can grow.
set -euo pipefail
it=$1; runs=${2:-1}; par=${3:-4}
here=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$it"
claude --version > "$it/harness.txt"
configs=${CONFIGS:-$(python3 -c "import json; print(' '.join(json.load(open('$here/configs.json'))))")}

python3 - "$here/evals.json" "$it" "$runs" $configs <<'P' | xargs -0 -n3 -P"$par" sh -c 'python3 "$0/run_trial.py" "$1" "$2" "$3" > "$3.log" 2>&1' "$here"
import json, os, sys
evals, it, runs, configs = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4:]
for e in json.load(open(evals))["evals"]:
    d = f"{it}/eval-{e['id']}-{e['name']}"
    os.makedirs(d, exist_ok=True)
    json.dump({"eval_id": e["id"], "eval_name": e["name"], "prompt": e["prompt"],
               "assertions": e["assertions"]}, open(f"{d}/eval_metadata.json", "w"), indent=2)
    for cfg in configs:
        for r in range(1, runs + 1):
            os.makedirs(f"{d}/{cfg}", exist_ok=True)
            if os.path.exists(f"{d}/{cfg}/run-{r}/timing.json"):
                continue
            sys.stdout.write("\0".join([str(e["id"]), cfg, f"{d}/{cfg}/run-{r}"]) + "\0")
P
