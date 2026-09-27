#!/usr/bin/env python3
"""Export a graded eval run and render it as a paper-style report.

Usage:
  export_results.py export <run-dir> <out-dir> --version V --model M [--harness H]
  export_results.py render <out-dir>

`export` copies per run grading.json, timing.json, the agent's reply and the
resulting git history (no repos, raw transcripts or session ids), scrubs
local paths, writes summary.json and renders README.md. `render` rebuilds
README.md from an existing export, e.g. after editing paper.md.
"""
import argparse, json, math, re, shutil, statistics as st
from collections import Counter
from datetime import date
from math import comb
from pathlib import Path

from skill_usage import skills_invoked

HERE = Path(__file__).resolve().parent
CONFIGS = ("with_skill", "without_skill")
LABELS = {"with_skill": "Skill", "without_skill": "Baseline"}
TARGET_SKILL = "commit"


def scrub(text):
    text = re.sub(r"/private/tmp/[^\s`'\"]*", "<tmp>", text)
    return text.replace(str(Path.home()), "~")


def eval_dirs(root):
    return sorted(Path(root).glob("eval-*"), key=lambda p: int(p.name.split("-")[1]))


def normalize_harness(version_line):
    """`claude --version` prints "2.1.283 (Claude Code)"; report "Claude Code 2.1.283"."""
    m = re.match(r"\s*([\d.]+) \((.+)\)", version_line)
    return f"{m.group(2)} {m.group(1)}" if m else version_line.strip()


def export(run_dir, out, version, model, harness):
    if out.exists():
        shutil.rmtree(out)
    invoked = {c: [0, 0] for c in CONFIGS}  # [target skill, other skill]
    for e in eval_dirs(run_dir):
        (out / e.name).mkdir(parents=True)
        shutil.copy(e / "eval_metadata.json", out / e.name / "eval_metadata.json")
        for c in CONFIGS:
            for run in sorted((e / c).glob("run-*")):
                dst = out / e.name / c / run.name
                dst.mkdir(parents=True)
                shutil.copy(run / "timing.json", dst / "timing.json")
                (dst / "grading.json").write_text(scrub((run / "grading.json").read_text()))
                for f in ("response.md", "git_result.txt"):
                    (dst / f).write_text(scrub((run / "outputs" / f).read_text()))
                skills = skills_invoked(run / "outputs" / "raw.json") or []
                invoked[c][0] += TARGET_SKILL in skills
                invoked[c][1] += any(s != TARGET_SKILL for s in skills)
    harness_file = Path(run_dir) / "harness.txt"
    meta = {
        "skill_version": version,
        "model": model,
        "harness": harness or (normalize_harness(harness_file.read_text()) if harness_file.exists() else "unknown"),
        "date": date.today().isoformat(),
        "skill_invocations": {c: {"target": invoked[c][0], "other": invoked[c][1]} for c in CONFIGS},
    }
    (out / "summary.json").write_text(json.dumps(meta, indent=2) + "\n")


def wilson(k, n, z=1.96):
    p = k / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    denom = 1 + z * z / n
    return (centre - margin) / denom, (centre + margin) / denom


def fisher_two_sided(a, b, c, d):
    """Fisher's exact test for the 2x2 table [[a, b], [c, d]]."""
    row, col, n = a + b, a + c, a + b + c + d
    prob = lambda x: comb(row, x) * comb(n - row, col - x) / comb(n, col)
    observed = prob(a)
    return sum(prob(x) for x in range(max(0, col - (n - row)), min(row, col) + 1)
               if prob(x) <= observed * (1 + 1e-9))


def sign_test(wins, losses):
    n = wins + losses
    tail = sum(comb(n, i) for i in range(min(wins, losses) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def pct(x):
    return f"{x:.1%}"


def table(header, rows):
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    return "\n".join(lines + ["| " + " | ".join(map(str, r)) + " |" for r in rows])


def render(out):
    meta = json.loads((out / "summary.json").read_text())
    specs = {e["name"]: e for e in json.loads((HERE / "evals.json").read_text())["evals"]}
    per_eval, grades, timings = [], {c: [] for c in CONFIGS}, {c: [] for c in CONFIGS}
    for e in eval_dirs(out):
        name = e.name.split("-", 2)[2]
        row = {"id": e.name.split("-")[1], "name": name, "spec": specs[name]}
        for c in CONFIGS:
            runs = sorted((e / c).glob("run-*"))
            g = [json.loads((r / "grading.json").read_text()) for r in runs]
            grades[c] += g
            timings[c] += [json.loads((r / "timing.json").read_text()) for r in runs]
            row[c] = (sum(x["summary"]["failed"] == 0 for x in g), len(g))
        per_eval.append(row)

    trials = per_eval[0]["with_skill"][1]
    success = {c: sum(r[c][0] for r in per_eval) for c in CONFIGS}
    n = {c: sum(r[c][1] for r in per_eval) for c in CONFIGS}
    s, b = "with_skill", "without_skill"
    wins = sum(r[s][0] > r[b][0] for r in per_eval)
    losses = sum(r[s][0] < r[b][0] for r in per_eval)
    mean = lambda c, k: st.mean(t[k] for t in timings[c])
    sd = lambda c, k: st.stdev(t[k] for t in timings[c])

    def checks(c):
        passed = sum(g["summary"]["passed"] for g in grades[c])
        return f"{passed} of {sum(g['summary']['total'] for g in grades[c])}"

    def ci(c):
        lo, hi = wilson(success[c], n[c])
        return f"{pct(lo)}-{pct(hi)}"

    failures = {c: Counter(x["text"] for g in grades[c] for x in g["expectations"] if not x["passed"])
                for c in CONFIGS}
    failed_checks = sorted(set(failures[s]) | set(failures[b]),
                           key=lambda t: (-failures[b][t] - failures[s][t], t))
    fisher = fisher_two_sided(success[s], n[s] - success[s], success[b], n[b] - success[b])
    inv = meta.get("skill_invocations", {})
    measures = [("Cost (USD)", "cost_usd", "{:.3f}"), ("Output tokens", "output_tokens", "{:.0f}"),
                ("Agent turns", "num_turns", "{:.1f}"), ("Duration (s)", "total_duration_seconds", "{:.1f}")]
    day = date.fromisoformat(meta["date"])

    values = {
        "version": meta["skill_version"], "model": meta["model"], "harness": meta["harness"],
        "date_long": f"{day.day} {day:%B %Y}",
        "out_dir": Path(out).resolve().relative_to(HERE.parent.parent),
        "n_scenarios": len(per_eval), "trials": trials, "n_trials": n[s],
        "skill_pass": success[s], "base_pass": success[b],
        "skill_rate": pct(success[s] / n[s]), "base_rate": pct(success[b] / n[b]),
        "skill_ci": ci(s), "base_ci": ci(b),
        "skill_checks": checks(s), "base_checks": checks(b),
        "fisher_p": f"{fisher:.1e}" if fisher < 0.001 else f"{fisher:.3f}",
        "sign_wins": wins, "sign_losses": losses, "sign_ties": len(per_eval) - wins - losses,
        "sign_p": f"{sign_test(wins, losses):.4f}",
        "skill_cost": f"${mean(s, 'cost_usd'):.3f}", "base_cost": f"${mean(b, 'cost_usd'):.3f}",
        "turn_delta": f"{mean(s, 'num_turns') - mean(b, 'num_turns'):.1f}",
        "skill_invoked": f"{inv.get(s, {}).get('target', '?')} of {n[s]}",
        "base_other_skill": f"{inv.get(b, {}).get('other', '?')} of {n[b]}",
        "table_scenarios": table(["#", "Scenario", "Prompt", "Behavior tested"],
                                 [(r["id"], f"`{r['name']}`", f"\"{r['spec']['prompt']}\"", r["spec"]["tests"])
                                  for r in per_eval]),
        "table_results": table(["#", "Scenario", "Skill", "Baseline"],
                               [(r["id"], f"`{r['name']}`", f"{r[s][0]}/{r[s][1]}", f"{r[b][0]}/{r[b][1]}")
                                for r in per_eval]
                               + [("", "**Total**", f"**{success[s]}/{n[s]}**", f"**{success[b]}/{n[b]}**")]),
        "table_failures": table(["Check", "Skill", "Baseline"],
                                [(t, failures[s][t], failures[b][t]) for t in failed_checks]
                                or [("(none)", 0, 0)]),
        "table_cost": table(["Measure", "Skill", "Baseline"],
                            [(label, f"{fmt.format(mean(s, k))} ({fmt.format(sd(s, k))})",
                              f"{fmt.format(mean(b, k))} ({fmt.format(sd(b, k))})")
                             for label, k, fmt in measures]),
    }
    text = re.sub(r"<!--.*?-->\n", "", (HERE / "paper.md").read_text(), count=1, flags=re.S)
    text = re.sub(r"\{\{(\w+)\}\}", lambda m: str(values[m.group(1)]), text)
    (out / "README.md").write_text(text)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    ex = sub.add_parser("export")
    ex.add_argument("run_dir", type=Path)
    ex.add_argument("out", type=Path)
    ex.add_argument("--version", required=True)
    ex.add_argument("--model", required=True)
    ex.add_argument("--harness")
    sub.add_parser("render").add_argument("out", type=Path)
    args = ap.parse_args()
    if args.cmd == "export":
        export(args.run_dir, args.out, args.version, args.model, args.harness)
    render(args.out)
    print(f"rendered {args.out / 'README.md'}")
