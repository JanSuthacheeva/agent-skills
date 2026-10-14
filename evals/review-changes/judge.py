#!/usr/bin/env python3
"""Blind-judge the reports review methods leave for the branch owner.

Usage: judge.py <iteration-dir> [runs=1,2,3] [seed=0]

For every scenario and run, copies each config's final response and
repository into shuffled label directories under <iteration>/blind/
(copies, not links, because fixture paths name the config), asks a
headless judge to score them with judge.md, and writes the unblinded
verdict to <iteration>/judge/run-<n>/<scenario>.json.
"""
import json, os, random, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LABELS = ["X", "Y", "Z"]
COUNTS = {2: "two", 3: "three"}
CRITERIA = ["accuracy", "risk", "decisions", "readability"]
MODEL = os.environ.get("JUDGE_MODEL", "claude-opus-5-5")


def spec_for(scenario):
    eval_id = int(scenario.name.split("-")[1])
    return next(e for e in json.loads((HERE / "evals.json").read_text())["evals"] if e["id"] == eval_id)


def blind(scenario, run, rng, iteration):
    configs = sorted(p.parent.parent.name for p in scenario.glob(f"*/run-{run}/outputs"))
    rng.shuffle(configs)
    target = iteration / "blind" / f"run-{run}" / scenario.name
    shutil.rmtree(target, ignore_errors=True)
    key = {}
    for label, config in zip(LABELS, configs):
        source = scenario / config / f"run-{run}"
        dest = target / label
        dest.mkdir(parents=True)
        shutil.copy(source / "outputs" / "response.md", dest / "report.md")
        shutil.copytree((source / "repo").resolve(), dest / "repo", symlinks=True)
        key[label] = config
    return target, key


def judge(target, key, spec):
    labels = "\n".join(f"- {label}: {target / label}/" for label in key)
    planted = "\n".join(f"- {p}" for p in spec["planted"])
    prompt = (HERE / "judge.md").read_text().format(
        count=COUNTS[len(key)], task=spec["prompt"], planted=planted, labels=labels)
    prompt += f"\n\nDo not open anything outside {target}."
    result = subprocess.run(
        ["claude", "-p", prompt, "--output-format", "json", "--model", MODEL, "--effort", "medium",
         "--setting-sources", "project,local", "--strict-mcp-config", "--mcp-config", '{"mcpServers": {}}',
         "--disallowedTools", "AskUserQuestion", "--allowedTools", "Read", "Glob", "Grep", "Bash"],
        cwd=target, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    reply = json.loads(result.stdout or "{}")
    text = reply.get("result", "")
    verdict = json.loads(text[text.index("{"):text.rindex("}") + 1])
    return verdict, reply.get("total_cost_usd", 0)


def main():
    iteration = Path(sys.argv[1]).resolve()
    runs = (sys.argv[2] if len(sys.argv) > 2 else "1,2,3").split(",")
    rng = random.Random(int(sys.argv[3]) if len(sys.argv) > 3 else 0)
    for run in runs:
        for scenario in sorted(iteration.glob("eval-*")):
            spec = spec_for(scenario)
            target, key = blind(scenario, run, rng, iteration)
            verdict, cost = judge(target, key, spec)
            unblinded = {
                "scores": {key[label]: score for label, score in verdict["scores"].items()},
                "ranking": [key[label] for label in verdict["ranking"]],
                "reason": verdict.get("reason", ""), "key": key, "judge_cost_usd": cost}
            out = iteration / "judge" / f"run-{run}"
            out.mkdir(parents=True, exist_ok=True)
            (out / f"{scenario.name}.json").write_text(json.dumps(unblinded, indent=2))
            totals = {c: sum(s[k] for k in CRITERIA) for c, s in unblinded["scores"].items()}
            print(f"run-{run} {scenario.name:22} {totals} ranking {unblinded['ranking']}")


if __name__ == "__main__":
    main()
