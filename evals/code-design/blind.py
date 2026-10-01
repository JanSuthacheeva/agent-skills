"""Copy each scenario's final plans into blind, shuffled label directories.

Usage: blind.py <iteration-dir> [run=1] [seed=0]

Writes <iteration>/blind/<scenario>/<label>/page-N.html|plan-N.md, and
the label-to-config key to <iteration>/blind-keys/<scenario>.json, outside
the directory judges can see. The transcript is left out because its
first line names the method.
"""

import json
import random
import shutil
import sys
from pathlib import Path

LABELS = ["W", "X", "Y", "Z"]


def main():
    iteration = Path(sys.argv[1])
    run = sys.argv[2] if len(sys.argv) > 2 else "1"
    rng = random.Random(int(sys.argv[3]) if len(sys.argv) > 3 else 0)
    for scenario in sorted(iteration.glob("eval-*")):
        configs = sorted(p.parent.name for p in scenario.glob(f"*/run-{run}/outputs"))
        rng.shuffle(configs)
        target = iteration / "blind" / scenario.name
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
        keys = iteration / "blind-keys"
        keys.mkdir(exist_ok=True)
        (keys / f"{scenario.name}.json").write_text(json.dumps(key, indent=2))
        print(scenario.name, key)


if __name__ == "__main__":
    main()
