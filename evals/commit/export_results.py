#!/usr/bin/env python3
"""Export a graded eval run into a publishable results directory.

Usage: export_results.py <graded-run-dir> <out-dir> <skill-version> <model>

Copies per run grading.json, timing.json, the agent's reply and the
resulting git history (no repos, raw transcripts or session ids), scrubs
local paths and writes a README.md summary.
"""
import json, re, shutil, statistics as st, sys
from datetime import date
from pathlib import Path

src, out, version, model = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], sys.argv[4]
CONFIGS = ("with_skill", "without_skill")
home = str(Path.home())


def scrub(text):
    text = re.sub(r"/private/tmp/[^\s`'\"]*", "<tmp>", text)
    return text.replace(home, "~")


def order(p):
    return int(p.name.split("-")[1])


if out.exists():
    shutil.rmtree(out)
evals = sorted(src.glob("eval-*"), key=order)
rows, totals = [], {c: {"runs": [], "timing": []} for c in CONFIGS}
for e in evals:
    meta = json.loads((e / "eval_metadata.json").read_text())
    (out / e.name).mkdir(parents=True)
    (out / e.name / "eval_metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
    row = {"name": e.name, "prompt": meta["prompt"]}
    for c in CONFIGS:
        full = 0
        for run in sorted((e / c).glob("run-*")):
            dst = out / e.name / c / run.name
            dst.mkdir(parents=True)
            grading = json.loads((run / "grading.json").read_text())
            timing = json.loads((run / "timing.json").read_text())
            (dst / "grading.json").write_text(scrub(json.dumps(grading, indent=2)) + "\n")
            (dst / "timing.json").write_text(json.dumps(timing, indent=2) + "\n")
            for f in ("response.md", "git_result.txt"):
                (dst / f).write_text(scrub((run / "outputs" / f).read_text()))
            full += grading["summary"]["failed"] == 0
            totals[c]["runs"].append(grading["summary"])
            totals[c]["timing"].append(timing)
        row[c] = f"{full}/{len(list((e / c).glob('run-*')))}"
    rows.append(row)


def summary(c):
    runs, timing = totals[c]["runs"], totals[c]["timing"]
    mean = lambda k: st.mean(t[k] for t in timing)
    return {
        "all_checks_passed": f"{sum(r['failed'] == 0 for r in runs)}/{len(runs)}",
        "mean_pass_rate": f"{st.mean(r['pass_rate'] for r in runs):.1%}",
        "cost_usd": f"${mean('cost_usd'):.3f}",
        "output_tokens": f"{mean('output_tokens'):.0f}",
        "turns": f"{mean('num_turns'):.1f}",
        "seconds": f"{mean('total_duration_seconds'):.1f}",
    }


s = {c: summary(c) for c in CONFIGS}
(out / "summary.json").write_text(json.dumps(
    {"skill_version": version, "model": model, "date": date.today().isoformat(),
     "evals": rows, "totals": s}, indent=2) + "\n")

trials = len(list((evals[0] / CONFIGS[0]).glob("run-*")))
lines = [
    f"# Eval results: commit skill v{version}",
    "",
    f"{len(evals)} scenarios, {trials} trials each, run on {date.today().isoformat()} "
    f"with `{model}` in headless Claude Code (`claude -p`).",
    "",
    "The eval method is based on the evaluation workflow of Anthropic's "
    "[skill-creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator) "
    "skill (with-skill vs. baseline runs, graded assertions, benchmark), adapted "
    "for repeated headless trials against git fixtures.",
    "",
    "- **with skill**: the installed `commit` skill, loaded the normal way.",
    "- **without skill**: same environment with the skill hidden via "
    "`skillOverrides`, plus one system line asking for Scoped Commits "
    "(`<scope>: <description>`), so the baseline knows the target format.",
    "",
    "A trial counts as passed only if every check for its scenario passes. "
    "Checks are graded by `grade.py` from the resulting repository, not from "
    "what the agent says it did.",
    "",
    "| Scenario | Prompt | With skill | Without skill |",
    "|---|---|---|---|",
]
for r in rows:
    lines.append(f"| {r['name'].split('-', 2)[2]} | \"{r['prompt']}\" | {r['with_skill']} | {r['without_skill']} |")
lines += [
    "",
    "| Per trial (mean) | With skill | Without skill |",
    "|---|---|---|",
    f"| All checks passed | {s['with_skill']['all_checks_passed']} | {s['without_skill']['all_checks_passed']} |",
    f"| Checks passed | {s['with_skill']['mean_pass_rate']} | {s['without_skill']['mean_pass_rate']} |",
    f"| Cost | {s['with_skill']['cost_usd']} | {s['without_skill']['cost_usd']} |",
    f"| Output tokens | {s['with_skill']['output_tokens']} | {s['without_skill']['output_tokens']} |",
    f"| Turns | {s['with_skill']['turns']} | {s['without_skill']['turns']} |",
    f"| Duration | {s['with_skill']['seconds']}s | {s['without_skill']['seconds']}s |",
    "",
    "Each `eval-*/<config>/run-*/` holds `grading.json` (every check with "
    "evidence), `timing.json`, the agent's final reply (`response.md`) and the "
    "commits it produced (`git_result.txt`). Scenario definitions live in "
    "`../../evals.json`, fixtures in `../../setup_fixture.sh`.",
    "",
    "Agents were allowed only git, Read, Glob and Grep, so compound shell "
    "commands that mixed in other tools (`cat`, `grep`, `python3`) were denied; "
    "the agent then retried with allowed commands.",
    "",
    "## Reproduce",
    "",
    "```sh",
    "commit/evals/run_iteration.sh <run-dir> <fixture-dir> 5 8",
    "commit/evals/grade.py <run-dir>",
    f"commit/evals/export_results.py <run-dir> {out} {version} {model}",
    "```",
    "",
]
(out / "README.md").write_text("\n".join(lines))
print(f"exported {len(evals)} evals to {out}")
