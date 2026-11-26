#!/usr/bin/env python3
"""Compare two skill versions run as configs of one graded iteration.

Usage: compare_versions.py <iteration-dir> <out-dir> <old> <new>

Copies each run's grading.json, timing.json, reply and review_result.txt
(scrubbed, no repositories or transcripts) and the unblinded judge
verdicts to <out-dir>, and writes there `comparison.md`: successful
trials and failed checks per scenario, judge totals, resource use, and
how often the session invoked the harness's security review, counted
across the main session and its subagents.
"""
import json, shutil, statistics as st, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from export_results import scrub  # pyright: ignore[reportMissingImports]

PROJECTS = Path.home() / ".claude" / "projects"
CRITERIA = ("accuracy", "risk", "decisions", "readability")


def transcripts(raw):
    sid = json.loads(raw.read_text()).get("session_id")
    hits = list(PROJECTS.glob(f"*/{sid}.jsonl")) if sid else []
    if not hits:
        return []
    return [hits[0], *sorted(hits[0].with_suffix("").glob("subagents/*.jsonl"))]


def skills_used(raw):
    used = []
    for path in transcripts(raw):
        for line in path.read_text().splitlines():
            content = json.loads(line).get("message", {}).get("content")
            for block in content if isinstance(content, list) else []:
                if block.get("type") == "tool_use" and block["name"] == "Skill":
                    used.append(block["input"].get("skill"))
    return used


def mean_sd(values, fmt):
    if not values:
        return "n/a"
    sd = st.stdev(values) if len(values) > 1 else 0
    return f"{fmt.format(st.mean(values))} ({fmt.format(sd)})"


def table(header, rows):
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    return "\n".join(lines + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows])


def main():
    it, out, old, new = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], sys.argv[4]
    configs = (old, new)
    if out.exists():
        shutil.rmtree(out)
    scenarios = sorted(it.glob("eval-*"), key=lambda p: int(p.name.split("-")[1]))
    results, failures, timing, security = {}, {c: Counter() for c in configs}, {c: [] for c in configs}, {}
    for scenario in scenarios:
        (out / scenario.name).mkdir(parents=True)
        shutil.copy(scenario / "eval_metadata.json", out / scenario.name / "eval_metadata.json")
        for c in configs:
            ok = n = sec = 0
            for run in sorted((scenario / c).glob("run-*")):
                dst = out / scenario.name / c / run.name
                dst.mkdir(parents=True)
                grading = json.loads((run / "grading.json").read_text())
                (dst / "grading.json").write_text(scrub(json.dumps(grading, indent=2)))
                shutil.copy(run / "timing.json", dst / "timing.json")
                for f in (run / "outputs" / "response.md", run / "outputs" / "review_result.txt"):
                    if f.exists():
                        (dst / f.name).write_text(scrub(f.read_text()))
                n += 1
                ok += grading["summary"]["failed"] == 0
                for e in grading["expectations"]:
                    if not e["passed"]:
                        failures[c][(scenario.name, e["text"])] += 1
                timing[c].append(json.loads((run / "timing.json").read_text()))
                sec += "security-review" in skills_used(run / "outputs" / "raw.json")
            results[(scenario.name, c)] = (ok, n)
            security[(scenario.name, c)] = sec

    judged = {c: [] for c in configs}
    for verdict in sorted(it.glob("judge/run-*/*.json")):
        data = json.loads(verdict.read_text())
        dst = out / "judge" / verdict.parent.name / verdict.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        data.pop("key", None)
        dst.write_text(json.dumps(data, indent=2) + "\n")
        for c, s in data["scores"].items():
            judged[c].append((verdict.stem, sum(s[k] for k in CRITERIA), data["ranking"][0] == c))

    name = lambda s: s.split("-", 2)[2]
    parts = ["## Successful trials (all checks passed)\n",
             table(["Scenario", old, new, f"{new} invoked /security-review"],
                   [(name(s.name), "{}/{}".format(*results[(s.name, old)]), "{}/{}".format(*results[(s.name, new)]),
                     f"{security[(s.name, new)]}/{results[(s.name, new)][1]}") for s in scenarios]),
             "\n\n## Failed checks (number of trials)\n",
             table(["Version", "Scenario", "Check", "Trials"],
                   [(c, name(s), t, k) for c in configs for (s, t), k in sorted(failures[c].items())] or [("-", "-", "none", 0)])]
    if any(judged.values()):
        rows = []
        for scenario in scenarios:
            row = [name(scenario.name)]
            for c in configs:
                totals = [t for s, t, _ in judged[c] if s == scenario.name]
                row.append(mean_sd(totals, "{:.1f}") if totals else "n/a")
            rows.append(row)
        rows.append(["All", *[mean_sd([t for _, t, _ in judged[c]], "{:.1f}") for c in configs]])
        rows.append(["Ranked first", *[f"{sum(f for *_, f in judged[c])}/{len(judged[c])}" for c in configs]])
        parts += ["\n\n## Blind judge, owner report total of 40, mean (sd)\n", table(["Scenario", old, new], rows)]
    measures = [("Cost (USD)", "cost_usd", "{:.2f}"), ("Duration (s)", "total_duration_seconds", "{:.0f}"),
                ("Output tokens", "output_tokens", "{:.0f}"), ("Subagents", "subagents", "{:.1f}")]
    parts += ["\n\n## Resource use per trial, mean (sd)\n",
              table(["Measure", old, new], [(label, *[mean_sd([t.get(k, 0) for t in timing[c]], fmt) for c in configs])
                                             for label, k, fmt in measures])]
    (out / "comparison.md").write_text("\n".join(parts) + "\n")
    print((out / "comparison.md").read_text())


if __name__ == "__main__":
    main()
