#!/usr/bin/env python3
"""Export graded (and optionally judged) eval runs of one suite and render
its results report, for one or more models.

Usage:
  export_results.py export <suite> <out> --version V --run MODEL=RUN_DIR ... [--harness H]
  export_results.py render <suite> <out>

`export` copies per run grading.json, timing.json, the agent's reply and
the grader's *_result.txt (no repositories, raw transcripts or session
ids), and the unblinded judge verdicts if the run was judged, into
<out>/<model>/. Local paths are scrubbed. It writes summary.json and renders
README.md from <suite>/report.md. `render` rebuilds README.md from an
existing export, e.g. after editing report.md.

Configs found in the runs are compared against the first one, with_skill.
"""
import argparse, json, math, re, shutil, statistics as st
from collections import Counter
from datetime import date
from math import comb
from pathlib import Path

from skill_usage import skills_invoked  # pyright: ignore[reportMissingImports]

ROOT = Path(__file__).resolve().parent.parent.parent
ORDER = ("with_skill", "without_skill", "code_review")
LABELS = {"with_skill": "Skill", "without_skill": "Baseline", "code_review": "`/code-review`"}
KEYS = {"with_skill": "skill", "without_skill": "base", "code_review": "cr"}
CRITERIA = ("accuracy", "risk", "decisions", "readability")
MEASURES = [("Cost (USD)", "cost_usd", "{:.3f}"), ("Output tokens", "output_tokens", "{:.0f}"),
            ("Agent turns", "num_turns", "{:.1f}"), ("Duration (s)", "total_duration_seconds", "{:.1f}")]


def slug(model):
    m = re.search(r"(opus|sonnet|haiku|fable)", model)
    return m.group(1) if m else re.sub(r"\W+", "-", model)


def scrub(text):
    text = re.sub(r"/private/tmp/[^\s`'\"]*", "<tmp>", text)
    text = re.sub(r"/var/folders/[^\s`'\"]*", "<tmp>", text)
    text = re.sub(r"\S*/workspace/fixtures/[^\s`'\"]*", "<fixture>", text)
    return text.replace(str(Path.home()), "~")


def eval_dirs(root):
    return sorted(Path(root).glob("eval-*"), key=lambda p: int(p.name.split("-")[1]))


def configs_in(root):
    found = {c.name for e in eval_dirs(root) for c in e.iterdir() if c.is_dir()}
    return [c for c in ORDER if c in found]


def normalize_harness(line):
    m = re.match(r"\s*([\d.]+) \((.+)\)", line)
    return f"{m.group(2)} {m.group(1)}" if m else line.strip()


def export(suite, out, version, runs, harness):
    skill = json.loads((suite / "evals.json").read_text())["skill_name"]
    if out.exists():
        shutil.rmtree(out)
    meta = {"skill_version": version, "date": date.today().isoformat(), "models": {}}
    for model, run_dir in runs:
        dest_root = out / slug(model)
        invoked = {}
        for e in eval_dirs(run_dir):
            (dest_root / e.name).mkdir(parents=True)
            shutil.copy(e / "eval_metadata.json", dest_root / e.name / "eval_metadata.json")
            for c in configs_in(run_dir):
                count = invoked.setdefault(c, [0, 0])
                for run in sorted((e / c).resolve().glob("run-*")):
                    dst = dest_root / e.name / c / run.name
                    dst.mkdir(parents=True)
                    shutil.copy(run / "timing.json", dst / "timing.json")
                    (dst / "grading.json").write_text(scrub((run / "grading.json").read_text()))
                    for f in [run / "outputs" / "response.md", *sorted((run / "outputs").glob("*_result.txt"))]:
                        if f.exists():
                            (dst / f.name).write_text(scrub(f.read_text()))
                    skills = skills_invoked(run / "outputs" / "raw.json") or []
                    count[0] += skill in skills
                    count[1] += any(s != skill for s in skills)
        for verdict in sorted(Path(run_dir).glob("judge/run-*/*.json")):
            dst = dest_root / "judge" / verdict.parent.name / verdict.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            data = json.loads(verdict.read_text())
            data.pop("key", None)
            dst.write_text(json.dumps(data, indent=2) + "\n")
        harness_file = Path(run_dir) / "harness.txt"
        meta["harness"] = harness or (normalize_harness(harness_file.read_text()) if harness_file.exists() else "unknown")
        meta["models"][slug(model)] = {"model": model, "run_dir": str(Path(run_dir).resolve().relative_to(ROOT)),
                                       "skill_invocations": {c: {"target": v[0], "other": v[1]} for c, v in invoked.items()}}
    (out / "summary.json").write_text(json.dumps(meta, indent=2) + "\n")


def wilson(k, n, z=1.96):
    p = k / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (centre - margin) / (1 + z * z / n), (centre + margin) / (1 + z * z / n)


def fisher_two_sided(a, b, c, d):
    row, col, n = a + b, a + c, a + b + c + d
    prob = lambda x: comb(row, x) * comb(n - row, col - x) / comb(n, col)
    observed = prob(a)
    return sum(prob(x) for x in range(max(0, col - (n - row)), min(row, col) + 1) if prob(x) <= observed * (1 + 1e-9))


def sign_test(wins, losses):
    n = wins + losses
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(comb(n, i) for i in range(min(wins, losses) + 1)) / 2 ** n)


def pct(x):
    return f"{x:.1%}"


def pvalue(p):
    return f"{p:.1e}" if p < 0.001 else f"{p:.3f}"


def table(header, rows):
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    return "\n".join(lines + ["| " + " | ".join(map(str, r)) + " |" for r in rows])


def model_stats(root):
    configs = configs_in(root)
    per_eval, grades, timings = [], {c: [] for c in configs}, {c: [] for c in configs}
    for e in eval_dirs(root):
        row: dict = {"id": e.name.split("-")[1], "name": e.name.split("-", 2)[2]}
        for c in configs:
            g = [json.loads((r / "grading.json").read_text()) for r in sorted((e / c).glob("run-*"))]
            grades[c] += g
            timings[c] += [json.loads((r / "timing.json").read_text()) for r in sorted((e / c).glob("run-*"))]
            row[c] = (sum(x["summary"]["failed"] == 0 for x in g), len(g))
        per_eval.append(row)
    judge = {}
    for verdict in sorted(root.glob("judge/run-*/*.json")):
        data = json.loads(verdict.read_text())
        for c, scores in data["scores"].items():
            entry = judge.setdefault(c, {k: [] for k in (*CRITERIA, "total", "rank")})
            for k in CRITERIA:
                entry[k].append(scores[k])
            entry["total"].append(sum(scores[k] for k in CRITERIA))
            entry["rank"].append(data["ranking"].index(c) + 1)
    return configs, per_eval, grades, timings, judge


def render(suite, out):
    meta = json.loads((out / "summary.json").read_text())
    specs = {e["name"]: e for e in json.loads((suite / "evals.json").read_text())["evals"]}
    models = list(meta["models"])
    stats = {m: model_stats(out / m) for m in models}
    first = stats[models[0]]
    day = date.fromisoformat(meta["date"])
    values = {
        "version": meta["skill_version"], "harness": meta["harness"], "date_long": f"{day.day} {day:%B %Y}",
        "out_dir": Path(out).resolve().relative_to(ROOT), "n_scenarios": len(first[1]),
        "trials": first[1][0]["with_skill"][1],
        "table_scenarios": table(["#", "Scenario", "Prompt", "Behavior tested"],
                                 [(r["id"], f"`{r['name']}`", f"\"{specs[r['name']]['prompt']}\"", specs[r["name"]]["tests"])
                                  for r in first[1]]),
    }
    columns = [(m, c) for m in models for c in stats[m][0]]
    head = [f"{m.capitalize()} {LABELS[c]}" for m, c in columns]
    result_rows, failure_counts, cost_rows, judge_rows = [], {}, [], []
    for m in models:
        configs, per_eval, grades, timings, judge = stats[m]
        values[f"{m}_model"] = meta["models"][m]["model"]
        values[f"{m}_run_dir"] = meta["models"][m]["run_dir"]
        n_trials = sum(r["with_skill"][1] for r in per_eval)
        values[f"{m}_n_trials"] = n_trials
        for c in configs:
            k = f"{m}_{KEYS[c]}"
            success = sum(r[c][0] for r in per_eval)
            n = sum(r[c][1] for r in per_eval)
            passed = sum(g["summary"]["passed"] for g in grades[c])
            total = sum(g["summary"]["total"] for g in grades[c])
            lo, hi = wilson(success, n)
            mean = lambda key: st.mean(t[key] for t in timings[c])
            inv = meta["models"][m]["skill_invocations"].get(c, {})
            values.update({f"{k}_pass": success, f"{k}_n": n, f"{k}_rate": pct(success / n), f"{k}_ci": f"{pct(lo)}-{pct(hi)}",
                           f"{k}_checks": f"{passed} of {total}", f"{k}_cost": f"${mean('cost_usd'):.3f}",
                           f"{k}_duration": f"{mean('total_duration_seconds'):.0f} s",
                           f"{k}_invoked": f"{inv.get('target', '?')} of {n}", f"{k}_other_skill": f"{inv.get('other', '?')} of {n}"})
            for g in grades[c]:
                for x in g["expectations"]:
                    if not x["passed"]:
                        failure_counts.setdefault(x["text"], Counter())[(m, c)] += 1
            if c in judge:
                j = judge[c]
                values[f"{k}_judge"] = f"{st.mean(j['total']):.1f}"
                values[f"{k}_rank"] = f"{st.mean(j['rank']):.2f}"
                values[f"{k}_firsts"] = f"{j['rank'].count(1)} of {len(j['rank'])}"
                judge_rows.append((m.capitalize(), LABELS[c], *[f"{st.mean(j[x]):.1f}" for x in CRITERIA],
                                   f"{st.mean(j['total']):.1f} ({st.stdev(j['total']):.1f})", f"{st.mean(j['rank']):.2f}"))
        for c in configs[1:]:
            s, b = "with_skill", c
            a_s, n_s = sum(r[s][0] for r in per_eval), sum(r[s][1] for r in per_eval)
            a_b, n_b = sum(r[b][0] for r in per_eval), sum(r[b][1] for r in per_eval)
            wins = sum(r[s][0] > r[b][0] for r in per_eval)
            losses = sum(r[s][0] < r[b][0] for r in per_eval)
            k = f"{m}_vs_{KEYS[c]}"
            values.update({f"{k}_fisher_p": pvalue(fisher_two_sided(a_s, n_s - a_s, a_b, n_b - a_b)),
                           f"{k}_wins": wins, f"{k}_losses": losses, f"{k}_ties": len(per_eval) - wins - losses,
                           f"{k}_sign_p": f"{sign_test(wins, losses):.4f}"})
    for i, r in enumerate(first[1]):
        cells = [f"{stats[m][1][i][c][0]}/{stats[m][1][i][c][1]}" for m, c in columns]
        result_rows.append((r["id"], f"`{r['name']}`", *cells))
    totals = [f"**{sum(row[c][0] for row in stats[m][1])}/{sum(row[c][1] for row in stats[m][1])}**" for m, c in columns]
    result_rows.append(("", "**Total**", *totals))
    for label, key, fmt in MEASURES:
        cells = []
        for m, c in columns:
            t = [x[key] for x in stats[m][3][c]]
            if not any(t):
                cells.append("n/a")
                continue
            cells.append(f"{fmt.format(st.mean(t))} ({fmt.format(st.stdev(t) if len(t) > 1 else 0)})")
        cost_rows.append((label, *cells))
    failed = sorted(failure_counts, key=lambda t: (-sum(failure_counts[t].values()), t))
    values["table_results"] = table(["#", "Scenario", *head], result_rows)
    values["table_failures"] = table(["Check", *head], [(t, *[failure_counts[t][col] for col in columns]) for t in failed]
                                     or [("(none)", *[0] * len(columns))])
    values["table_cost"] = table(["Measure", *head], cost_rows)
    values["table_judge"] = table(["Model", "Condition", *[c.capitalize() for c in CRITERIA], "Total /40 (SD)", "Mean rank"],
                                  judge_rows) if judge_rows else ""
    text = re.sub(r"<!--.*?-->\n", "", (suite / "report.md").read_text(), count=1, flags=re.S)
    missing = sorted(set(re.findall(r"\{\{(\w+)\}\}", text)) - set(values))
    if missing:
        raise SystemExit(f"report.md uses unknown placeholders: {missing}")
    (out / "README.md").write_text(re.sub(r"\{\{(\w+)\}\}", lambda m: str(values[m.group(1)]), text))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    ex = sub.add_parser("export")
    ex.add_argument("suite", type=Path)
    ex.add_argument("out", type=Path)
    ex.add_argument("--version", required=True)
    ex.add_argument("--run", action="append", required=True, help="MODEL=RUN_DIR, repeatable")
    ex.add_argument("--harness")
    rd = sub.add_parser("render")
    rd.add_argument("suite", type=Path)
    rd.add_argument("out", type=Path)
    args = ap.parse_args()
    suite = args.suite.resolve()
    if args.cmd == "export":
        runs = [tuple(r.split("=", 1)) for r in args.run]
        export(suite, args.out, args.version, [(m, Path(d)) for m, d in runs], args.harness)
    render(suite, args.out)
    print(f"rendered {args.out / 'README.md'}")
