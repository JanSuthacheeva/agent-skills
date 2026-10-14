"""Copy each scenario's final plans into blind, shuffled label directories.

Usage: blind.py <iteration-dir> [run=1] [seed=0] [scenario-substring]

Writes <iteration>/blind/run-<run>/<scenario>/<label>/page-N.html|plan-N.md
with a judge-prompt.md next to them, and the label-to-config key to
<iteration>/blind-keys/run-<run>/<scenario>.json, outside the directory
judges can see. The transcript is left out because its
first line names the method.
"""

import json
import os
import random
import shutil
import sys
from pathlib import Path

LABELS = ["W", "X", "Y", "Z"]
HERE = Path(__file__).resolve().parent
EVALS_FILE = Path(os.environ.get("EVALS_FILE", HERE / "evals.json"))
COUNTS = {2: "two", 3: "three", 4: "four"}


def write_judge_prompt(scenario: Path, target: Path, labels: list[str]):
    eval_id = int(scenario.name.split("-")[1])
    spec = next(e for e in json.loads(EVALS_FILE.read_text())["evals"] if e["id"] == eval_id)
    repo = HERE / "workspace" / "fixtures" / spec["fixture"]["name"]
    plans = "\n".join(f"- {label}: {target / label}/" for label in labels)
    count = COUNTS[len(labels)]
    prompt = (HERE / "judge.md").read_text().format(task=spec["prompt"], repo=repo, plans=plans, count=count)
    if len(labels) < len(LABELS):
        listed = " and ".join(labels)
        prompt += f"\n\nOnly the plans {listed} exist; score and rank just those in the JSON."
    prompt += (f"\n\nWrite the JSON to {target / 'verdict.json'} as well as replying with it. "
               f"Do not open anything outside the {count} plan directories and the repository.")
    (target / "judge-prompt.md").write_text(prompt)


def main():
    iteration = Path(sys.argv[1]).resolve()
    run = sys.argv[2] if len(sys.argv) > 2 else "1"
    rng = random.Random(int(sys.argv[3]) if len(sys.argv) > 3 else 0)
    only = sys.argv[4] if len(sys.argv) > 4 else ""
    for scenario in sorted(iteration.glob("eval-*")):
        if only not in scenario.name:
            continue
        configs = sorted(p.parent.parent.name for p in scenario.glob(f"*/run-{run}/outputs"))
        rng.shuffle(configs)
        target = iteration / "blind" / f"run-{run}" / scenario.name
        shutil.rmtree(target, ignore_errors=True)
        key = {}
        for label, config in zip(LABELS, configs):
            outputs = scenario / config / f"run-{run}" / "outputs"
            dest = target / label
            dest.mkdir(parents=True)
            for kind, suffix in (("page", ".html"), ("plan", ".md")):
                files = sorted(f for f in outputs.iterdir() if f.suffix == suffix and f.name != "transcript.md")
                for n, f in enumerate(files, 1):
                    shutil.copy2(f, dest / f"{kind}-{n}{suffix}")
            key[label] = config
        write_judge_prompt(scenario, target, list(key))
        keys = iteration / "blind-keys" / f"run-{run}"
        keys.mkdir(parents=True, exist_ok=True)
        (keys / f"{scenario.name}.json").write_text(json.dumps(key, indent=2))
        print(scenario.name, key)


if __name__ == "__main__":
    main()
