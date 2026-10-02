#!/usr/bin/env python3
"""Export a graded and judged eval iteration and render it as a report.

Usage:
  export_results.py export <iteration-dir> <out-dir> --version V --model M
  export_results.py render <out-dir>

`export` copies per run grading.json, timing.json and meta.json, the
unblinded judge verdicts and, for public scenarios, the final plan files
and the conversation with the simulated user. Scenarios marked "private"
in evals.json keep only scores: no plans, transcripts, grading evidence or
judge notes. Local paths and session ids are scrubbed. It then writes
summary.json and renders README.md from report.md.
"""

import argparse
import json
import math
import re
import shutil
import statistics as st
from datetime import date
from math import comb
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIGS = ("code-design", "feature-dev", "superpowers", "plain")
TARGET = "code-design"
CRITERIA = ("correctness", "completeness", "clarity", "reviewability")


def scrub(text):
    text = re.sub(r"/private/tmp/[^\s`'\")]*", "<tmp>", text)
    text = re.sub(r"[^\s`'\"(]*/evals/code-design/workspace/[^\s`'\")]*", "<run>", text)
    return text.replace(str(Path.home()), "~")


def scenarios():
    return {f"eval-{e['id']}-{e['name']}": e for e in json.loads((HERE / "evals.json").read_text())["evals"]}


def normalize_harness(version_line):
    m = re.match(r"\s*([\d.]+) \((.+)\)", version_line)
    return f"{m.group(2)} {m.group(1)}" if m else version_line.strip()


def public_grading(grading, private):
    if not private:
        return json.loads(scrub(json.dumps(grading)))
    return {"expectations": [{"text": e["text"], "passed": e["passed"]} for e in grading["expectations"]],
            "summary": grading["summary"]}


def export_run(run, dst, private):
    dst.mkdir(parents=True)
    shutil.copy(run / "timing.json", dst / "timing.json")
    meta = json.loads((run / "meta.json").read_text())
    meta.pop("session_id", None)
    (dst / "meta.json").write_text(json.dumps(meta, indent=2))
    grading = json.loads((run / "grading.json").read_text())
    (dst / "grading.json").write_text(json.dumps(public_grading(grading, private), indent=2))
    if private:
        return
    plans = dst / "plans"
    plans.mkdir()
    for f in sorted((run / "outputs").iterdir()):
        if f.suffix in (".html", ".md") and f.name != "transcript.md":
            (plans / f.name).write_text(scrub(f.read_text(errors="ignore")))
    (dst / "transcript.md").write_text(scrub((run / "outputs" / "transcript.md").read_text()))


def unblinded_verdict(verdict, key, private):
    scores = {key[label]: {c: s[c] for c in CRITERIA} | ({} if private else {"note": s.get("note", "")})
              for label, s in verdict["scores"].items()}
    out = {"scores": scores, "ranking": [key[label] for label in verdict["ranking"]]}
    if not private:
        out["reason"] = verdict.get("reason", "")
    return out


def export(iteration, out, version, model):
    if out.exists():
        shutil.rmtree(out)
    specs = scenarios()
    for scenario in sorted(iteration.glob("eval-*"), key=lambda p: int(p.name.split("-")[1])):
        spec = specs[scenario.name]
        private = spec.get("private", False)
        (out / scenario.name).mkdir(parents=True)
        meta = json.loads((scenario / "eval_metadata.json").read_text())
        meta["preferences"] = spec["preferences"]
        meta["private"] = private
        (out / scenario.name / "eval_metadata.json").write_text(json.dumps(meta, indent=2))
        for config in CONFIGS:
            for run in sorted((scenario / config).glob("run-[0-9]*")):
                if run.is_dir() and (run / "grading.json").exists():
                    export_run(run, out / scenario.name / config / run.name, private)
        for verdict_file in sorted(iteration.glob(f"blind/run-*/{scenario.name}/verdict.json")):
            run_name = verdict_file.parent.parent.name
            key = json.loads((iteration / "blind-keys" / run_name / f"{scenario.name}.json").read_text())
            verdict = unblinded_verdict(json.loads(verdict_file.read_text()), key, private)
            dst = out / scenario.name / "verdicts"
            dst.mkdir(exist_ok=True)
            (dst / f"{run_name}.json").write_text(json.dumps(verdict, indent=2))
    harness = normalize_harness((iteration / "harness.txt").read_text())
    summary = summarize(out, version, model, harness)
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    render(out)


def mean_sd(values):
    return (st.mean(values), st.stdev(values) if len(values) > 1 else 0.0) if values else (0.0, 0.0)


def failed_checks(out, config):
    counts = {}
    for grading in out.glob(f"eval-*/{config}/run-*/grading.json"):
        for e in json.loads(grading.read_text())["expectations"]:
            if not e["passed"]:
                name = e["text"].split(":")[0]
                counts[name] = counts.get(name, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: -kv[1]))


def chi2_sf_df3(x):
    """Survival function of the chi-squared distribution with 3 degrees of freedom."""
    return math.erfc(math.sqrt(x / 2)) + math.sqrt(2 * x / math.pi) * math.exp(-x / 2)


def wilcoxon(diffs):
    """Exact two-sided Wilcoxon signed-rank test; zero differences are dropped."""
    d = [x for x in diffs if x != 0]
    n = len(d)
    if n == 0:
        return 1.0
    order = sorted(range(n), key=lambda i: abs(d[i]))
    ranks, i = [0.0] * n, 0
    while i < n:
        j = i
        while j + 1 < n and abs(d[order[j + 1]]) == abs(d[order[i]]):
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2 + 1
        i = j + 1
    total = n * (n + 1) / 2
    positive = sum(r for r, x in zip(ranks, d) if x > 0)
    observed = min(positive, total - positive)
    extreme = 0
    for mask in range(2 ** n):
        w = sum(ranks[k] for k in range(n) if mask >> k & 1)
        extreme += min(w, total - w) <= observed + 1e-9
    return extreme / 2 ** n


def sign_test(wins, losses):
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def summarize(out, version, model, harness):
    runs, blocks, block_scores = {c: [] for c in CONFIGS}, [], []
    per_scenario, criteria = {}, {c: {k: [] for k in CRITERIA} for c in CONFIGS}
    for scenario in sorted(p for p in out.glob("eval-*") if p.is_dir()):
        per_scenario[scenario.name] = {c: {"judge": [], "ranks": [], "checks": [0, 0]} for c in CONFIGS}
        for config in CONFIGS:
            for run in sorted((scenario / config).glob("run-*")):
                timing = json.loads((run / "timing.json").read_text())
                grading = json.loads((run / "grading.json").read_text())["summary"]
                meta = json.loads((run / "meta.json").read_text())
                runs[config].append({"timing": timing, "checks": grading, "meta": meta})
                per_scenario[scenario.name][config]["checks"][0] += grading["passed"]
                per_scenario[scenario.name][config]["checks"][1] += grading["total"]
        for verdict_file in sorted((scenario / "verdicts").glob("run-*.json")):
            verdict = json.loads(verdict_file.read_text())
            ranks = {c: verdict["ranking"].index(c) + 1 for c in CONFIGS}
            blocks.append(ranks)
            block_scores.append({c: sum(verdict["scores"][c][k] for k in CRITERIA) for c in CONFIGS})
            for c in CONFIGS:
                per_scenario[scenario.name][c]["judge"].append(sum(verdict["scores"][c][k] for k in CRITERIA))
                for k in CRITERIA:
                    criteria[c][k].append(verdict["scores"][c][k])
                per_scenario[scenario.name][c]["ranks"].append(ranks[c])

    configs = {}
    for c in CONFIGS:
        judge = [s for scen in per_scenario.values() for s in scen[c]["judge"]]
        ranks = [b[c] for b in blocks]
        cost = [r["timing"]["cost_usd"] for r in runs[c]]
        configs[c] = {
            "runs": len(runs[c]),
            "judge_mean": mean_sd(judge)[0], "judge_sd": mean_sd(judge)[1],
            "rank_mean": mean_sd(ranks)[0], "first_places": ranks.count(1),
            "checks_passed": sum(r["checks"]["passed"] for r in runs[c]),
            "checks_total": sum(r["checks"]["total"] for r in runs[c]),
            "cost_mean": mean_sd(cost)[0], "cost_sd": mean_sd(cost)[1],
            "tokens_mean": mean_sd([r["timing"]["total_tokens"] for r in runs[c]])[0],
            "subagent_tokens_mean": mean_sd([r["timing"]["subagent_tokens"] for r in runs[c]])[0],
            "output_tokens_mean": mean_sd([r["timing"]["output_tokens"] for r in runs[c]])[0],
            "cache_read_tokens_mean": mean_sd([r["timing"]["cache_read_tokens"] for r in runs[c]])[0],
            "turns_mean": mean_sd([r["timing"]["executor_turns"] for r in runs[c]])[0],
            "duration_mean": mean_sd([r["timing"]["total_duration_seconds"] for r in runs[c]])[0],
            "approved": sum(r["meta"]["approved"] for r in runs[c]),
            "touched_code": sum(bool(r["meta"]["touched_code"]) for r in runs[c]),
            "criteria": {k: mean_sd(v)[0] for k, v in criteria[c].items()},
            "score_per_dollar": mean_sd(judge)[0] / mean_sd(cost)[0] if cost else 0.0,
            "failed_checks": failed_checks(out, c),
        }

    n, k = len(blocks), len(CONFIGS)
    rank_sums = {c: sum(b[c] for b in blocks) for c in CONFIGS}
    friedman = 12 / (n * k * (k + 1)) * sum(r ** 2 for r in rank_sums.values()) - 3 * n * (k + 1) if n else 0.0
    pairwise = {}
    for other in CONFIGS:
        if other == TARGET:
            continue
        wins = sum(b[TARGET] < b[other] for b in blocks)
        losses = sum(b[TARGET] > b[other] for b in blocks)
        diffs = [b[TARGET] - b[other] for b in block_scores]
        pairwise[other] = {
            "rank_wins": wins, "rank_losses": losses, "rank_p": sign_test(wins, losses),
            "score_diffs": diffs, "score_mean_diff": st.mean(diffs) if diffs else 0.0,
            "score_wins": sum(x > 0 for x in diffs), "score_losses": sum(x < 0 for x in diffs),
            "score_ties": diffs.count(0), "score_p": wilcoxon(diffs),
        }

    return {
        "skill_version": version, "model": model, "harness": harness,
        "date": date.today().isoformat(), "n_scenarios": len(per_scenario),
        "runs_per_cell": max(len(v) for v in runs.values()) // max(len(per_scenario), 1),
        "n_blocks": n, "configs": configs, "per_scenario": per_scenario,
        "friedman": {"chi2": friedman, "df": k - 1, "p": chi2_sf_df3(friedman) if n else 1.0},
        "pairwise_vs_target": pairwise,
    }


def fmt_p(p):
    return f"{p:.2g}" if p >= 0.001 else f"{p:.1e}"


def tables(summary):
    c = summary["configs"]
    rows = ["| Method | Judge score (of 40) | Assertions passed | Cost per run (USD) | Judge score per USD |",
            "|---|---|---|---|---|"]
    for name in CONFIGS:
        v = c[name]
        rows.append(f"| `{name}` | {v['judge_mean']:.1f} ({v['judge_sd']:.1f}) | {v['checks_passed']}/{v['checks_total']} | "
                    f"{v['cost_mean']:.2f} ({v['cost_sd']:.2f}) | {v['score_per_dollar']:.1f} |")
    overall = "\n".join(rows)

    rows = ["| Method | Mean rank | First places |", "|---|---|---|"]
    for name in CONFIGS:
        v = c[name]
        rows.append(f"| `{name}` | {v['rank_mean']:.2f} | {v['first_places']}/{summary['n_blocks']} |")
    ranks_table = "\n".join(rows)

    rows = ["| Scenario | " + " | ".join(f"`{n}`" for n in CONFIGS) + " |", "|---|" + "---|" * len(CONFIGS)]
    for scen, data in summary["per_scenario"].items():
        cells = [f"{st.mean(data[n]['judge']):.1f} / {st.mean(data[n]['ranks']):.1f}" if data[n]["judge"] else "-"
                 for n in CONFIGS]
        rows.append(f"| `{scen.split('-', 2)[2]}` | " + " | ".join(cells) + " |")
    scenarios_table = "\n".join(rows)

    rows = ["| Measure | " + " | ".join(f"`{n}`" for n in CONFIGS) + " |", "|---|" + "---|" * len(CONFIGS)]
    for label, key, fmt in (("Cost (USD)", "cost_mean", "{:.2f}"), ("Tokens excl. cache reads", "tokens_mean", "{:,.0f}"),
                            ("of which in subagents", "subagent_tokens_mean", "{:,.0f}"),
                            ("Output tokens", "output_tokens_mean", "{:,.0f}"),
                            ("Cache reads", "cache_read_tokens_mean", "{:,.0f}"), ("Executor turns", "turns_mean", "{:.1f}"),
                            ("Duration (min)", "duration_mean", "{:.1f}")):
        scale = 60 if key == "duration_mean" else 1
        rows.append(f"| {label} | " + " | ".join(fmt.format(c[n][key] / scale) for n in CONFIGS) + " |")
    cost_table = "\n".join(rows)

    rows = ["| Compared with | Mean score difference | `code-design` higher / lower / equal | Wilcoxon p |",
            "|---|---|---|---|"]
    for other, v in summary["pairwise_vs_target"].items():
        rows.append(f"| `{other}` | {v['score_mean_diff']:+.1f} | {v['score_wins']} / {v['score_losses']} / "
                    f"{v['score_ties']} | {fmt_p(v['score_p'])} |")
    pairwise_table = "\n".join(rows)

    rows = ["| Compared with | `code-design` ranked higher | ranked lower | Sign test p |", "|---|---|---|---|"]
    for other, v in summary["pairwise_vs_target"].items():
        rows.append(f"| `{other}` | {v['rank_wins']} | {v['rank_losses']} | {fmt_p(v['rank_p'])} |")
    rank_pairwise_table = "\n".join(rows)

    rows = ["| Criterion | " + " | ".join(f"`{n}`" for n in CONFIGS) + " |", "|---|" + "---|" * len(CONFIGS)]
    for k in CRITERIA:
        rows.append(f"| {k.capitalize()} | " + " | ".join(f"{c[n]['criteria'][k]:.2f}" for n in CONFIGS) + " |")
    criteria_table = "\n".join(rows)

    names = sorted({k for n in CONFIGS for k in c[n]["failed_checks"]})
    rows = ["| Assertion | " + " | ".join(f"`{n}`" for n in CONFIGS) + " |", "|---|" + "---|" * len(CONFIGS)]
    for k in names:
        rows.append(f"| {k} | " + " | ".join(str(c[n]["failed_checks"].get(k, 0)) for n in CONFIGS) + " |")
    failures_table = "\n".join(rows)
    return (overall, scenarios_table, cost_table, pairwise_table, criteria_table, failures_table,
            ranks_table, rank_pairwise_table)


def render(out):
    summary = json.loads((out / "summary.json").read_text())
    (overall, scenarios_table, cost_table, pairwise_table, criteria_table, failures_table,
     ranks_table, rank_pairwise_table) = tables(summary)
    c = summary["configs"]
    best = min(CONFIGS, key=lambda n: c[n]["rank_mean"])
    values = {
        "version": summary["skill_version"], "model": summary["model"], "harness": summary["harness"],
        "date_long": date.fromisoformat(summary["date"]).strftime("%-d %B %Y"),
        "n_scenarios": summary["n_scenarios"], "runs": summary["runs_per_cell"], "n_blocks": summary["n_blocks"],
        "n_runs": sum(v["runs"] for v in c.values()),
        "target_judge": f"{c[TARGET]['judge_mean']:.1f}", "target_rank": f"{c[TARGET]['rank_mean']:.2f}",
        "target_firsts": c[TARGET]["first_places"], "best": best,
        "friedman_chi2": f"{summary['friedman']['chi2']:.2f}", "friedman_p": fmt_p(summary["friedman"]["p"]),
        "cost_ratio_plain": f"{c[TARGET]['cost_mean'] / c['plain']['cost_mean']:.1f}",
        "cost_ratio_feature_dev": f"{c[TARGET]['cost_mean'] / c['feature-dev']['cost_mean']:.1f}",
        "table_overall": overall, "table_scenarios": scenarios_table,
        "table_cost": cost_table, "table_pairwise": pairwise_table,
        "table_criteria": criteria_table, "table_failures": failures_table,
        "table_ranks": ranks_table, "table_rank_pairwise": rank_pairwise_table,
        "runs_per_method": c[TARGET]["runs"],
    }
    for name in CONFIGS:
        slug = name.replace("-", "_")
        values[f"{slug}_judge"] = f"{c[name]['judge_mean']:.1f}"
        values[f"{slug}_rank"] = f"{c[name]['rank_mean']:.2f}"
        values[f"{slug}_cost"] = f"{c[name]['cost_mean']:.2f}"
        values[f"{slug}_checks"] = f"{c[name]['checks_passed']}/{c[name]['checks_total']}"
        values[f"{slug}_per_dollar"] = f"{c[name]['score_per_dollar']:.1f}"
    for other, v in summary["pairwise_vs_target"].items():
        slug = other.replace("-", "_")
        values[f"vs_{slug}_diff"] = f"{v['score_mean_diff']:+.1f}"
        values[f"vs_{slug}_p"] = fmt_p(v["score_p"])
    template = (HERE / "report.md").read_text()
    template = re.sub(r"\A<!--.*?-->\n", "", template, flags=re.S)
    text = re.sub(r"\{\{(\w+)\}\}", lambda m: str(values[m.group(1)]), template)
    (out / "README.md").write_text(text)


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    exp = sub.add_parser("export")
    exp.add_argument("iteration", type=Path)
    exp.add_argument("out", type=Path)
    exp.add_argument("--version", required=True)
    exp.add_argument("--model", required=True)
    ren = sub.add_parser("render")
    ren.add_argument("out", type=Path)
    args = parser.parse_args()
    if args.cmd == "export":
        export(args.iteration.resolve(), args.out, args.version, args.model)
    else:
        render(args.out)


if __name__ == "__main__":
    main()
