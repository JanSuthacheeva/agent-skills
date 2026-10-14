#!/usr/bin/env python3
"""Grade ship-feature eval runs from each run's repository, the forge stub
log, the bare remote, the session transcript (for which steps ran in a
fresh agent and what that agent was told) and the flow stub's log, one
argv per call. The eval's flow_assertions are graded only for trials run
with the flow stub.

Usage: grade.py <iteration-dir>
Writes <run>/grading.json and <run>/outputs/flow_result.txt for every run.
"""
import json, os, re, subprocess, sys, tempfile
from pathlib import Path

PLAN = "docs/plans/2026-10-14-bookmark-tags.md"
LABELS = r"(Fixed|Open|Where\ to\ look)"
EMPTY = r"""(?i:(?:none|nothing)\b.*
    | no\ (?:\w+\ )?(?:items?|findings?|questions?|issues?)(?:\ (?:left|remain(?:s|ing)?|open))?\W*$)"""
NONE = rf"(?:{EMPTY})?"
REVIEW_LABEL = re.compile(rf"""^(?:
      \#+\s*{LABELS}\b                                            # ### Fixed
    | (?:\*\*|__){LABELS}(?:\ \w+)?:?(?:\*\*|__)                  # **Fixed** (commit ...), **Open questions**, **Fixed:**
    | \s*[-*]\s+(?:\*\*|__){LABELS}(?:\ \w+)?:?(?:\*\*|__):?\s*{NONE}$  # - **Open questions**, - **Open:** none
    | {LABELS}(?:\ \w+)?(?:\ \([^)\n]*\))?(?:\s*$|:)              # Fixed, Open questions:, Fixed (`0e06f9c`):
    | \s*[-*]\s+{LABELS}:\s*{NONE}$                                # - Open:, - Open: none
    )""", re.X)
LIST_ITEM = re.compile(rf"^(\s*)(?:[-*]|\d+[.)])\s+(?!{EMPTY})\S", re.X)
BUILD_REPORT = re.compile(r"deviation|I (built|implemented)|has been (built|implemented)|tasks? \d+ (to|-) \d+ (are|were) (done|built)", re.I)


def sh(cwd, *args, env=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=env, timeout=300)


def git(repo, *args):
    return sh(repo, "git", *args).stdout


def agent_calls(sid):
    """Agent tool calls of the main session, in order: (prompt, description)."""
    hits = list(Path.home().glob(f".claude/projects/*/{sid}.jsonl")) if sid else []
    calls = []
    for line in hits[0].read_text().splitlines() if hits else []:
        msg = json.loads(line).get("message", {})
        for part in msg.get("content", []) if isinstance(msg.get("content"), list) else []:
            if part.get("type") == "tool_use" and part.get("name") in ("Agent", "Task"):
                inp = part.get("input", {})
                calls.append((inp.get("prompt", ""), inp.get("description", "")))
    return calls


def boxes(repo):
    plan = (repo / PLAN).read_text() if (repo / PLAN).exists() else ""
    return re.findall(r"^- \[([ x])\]", plan, re.M), plan


def flow_reports(fx: Path) -> list[list[str]] | None:
    """The flow stub's log as argument lists after `report`, in order;
    None when the trial ran without flow."""
    log = fx / "flow.jsonl"
    if not log.exists():
        return None
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    return [args[1:] if args[:1] == ["report"] else args for args in calls]


def review_counts(plan: str) -> tuple[int, int]:
    """Findings under Fixed and Open in the plan's ## Review: the list items
    at the outermost level of each, so details nested under a finding do
    not count, nor does an item saying there is none. A label is a heading,
    a bold label or an unindented line starting with one; a list item is a
    label only when it holds nothing else, so `- Fixed duplicate tags: ...`
    stays a finding."""
    m = re.search(r"^## Review\s*$(.*?)(?=^## |\Z)", plan, re.M | re.S)
    indents: dict[str, list[int]] = {"fixed": [], "open": [], "where to look": []}
    current = None
    for line in (m.group(1) if m else "").splitlines():
        label = REVIEW_LABEL.match(line)
        item = LIST_ITEM.match(line)
        if label:
            current = indents[next(g for g in label.groups() if g).lower()]
        elif current is not None and item:
            current.append(len(item.group(1)))
    outermost = lambda found: sum(i == min(found) for i in found) if found else 0
    return outermost(indents["fixed"]), outermost(indents["open"])


def flow_check(t: str, reports: list[list[str]], plan: str) -> tuple[bool, str]:
    phases = []
    for i, r in enumerate(reports):
        if r[:1] == ["phase"] and len(r) > 1 and (not phases or phases[-1][1] != r[1]):
            phases.append((i, r[1]))
    reviews = [(i, r) for i, r in enumerate(reports) if r[:1] == ["review"]]
    fixed, open_ = review_counts(plan)
    if t.startswith("Reported the phase"):
        expected = ["implement", "review"] if "implement" in t else ["review"]
        expected += ["merge-request"] if open_ == 0 else []
        seen = [p for _, p in phases]
        return seen == expected, f"phases: {seen}; expected {expected} ({open_} open)"
    if t.startswith("Reported tasks 5 5"):
        tasks = [" ".join(r[1:]) for r in reports if r[:1] == ["tasks"]]
        return "5 5" in tasks, f"tasks: {tasks}"
    if t.startswith("Reported the review counts"):
        got = " ".join(reviews[-1][1][1:]) if reviews else None
        want = f"--fixed {fixed} --open {open_}"
        return got == want, f"reported: {got}; plan: {want}"
    if t.startswith("Reported the final stop"):
        if open_ > 0:
            after = reviews[-1][0] if reviews else len(reports)
            stop = [" ".join(r) for r in reports[after:] if r[:1] == ["blocked"] and len(r) == 2]
        else:
            after = max((i for i, p in phases if p == "merge-request"), default=len(reports))
            stop = [" ".join(r) for r in reports[after:] if r[:1] == ["waiting"] and len(r) == 2 and r[1].endswith("?")]
        return bool(stop), f"{open_} open; stop: {stop[-1] if stop else None}"
    raise ValueError(t)


def stored_tags(repo):
    with tempfile.TemporaryDirectory() as tmp:
        file = Path(tmp) / "store"
        env = {**os.environ, "BM_FILE": str(file)}
        sh(repo, "node", "src/main.ts", "add", "https://a.dev", "A", env=env)
        sh(repo, "node", "src/main.ts", "tag", "1", "work", env=env)
        sh(repo, "node", "src/main.ts", "tag", "1", "work", env=env)
        return json.loads(file.read_text())[0].get("tags") if file.exists() else None


def check(t, ctx):
    repo = ctx["repo"]
    build = [c for c in ctx["calls"] if re.search(r"implement-plan", c[0]) or re.search(r"\bbuild", c[1], re.I)]
    review = [c for c in ctx["calls"] if re.search(r"review-changes", c[0])
              and not re.search(r"\bfix", c[1], re.I)]
    if t.startswith("The task 1 commit is kept"):
        kept = sh(repo, "git", "merge-base", "--is-ancestor", ctx["branch_sha"], "HEAD").returncode == 0
        b, _ = boxes(repo)
        return kept and b == ["x"] * 5, f"task 1 commit kept: {kept}; boxes: {''.join(b)}"
    if t.startswith("No task was rebuilt"):
        kept = sh(repo, "git", "merge-base", "--is-ancestor", ctx["branch_sha"], "HEAD").returncode == 0
        return kept and not build, f"branch kept: {kept}; build agents: {len(build)}"
    if t == "The build ran in a fresh agent":
        return bool(build), f"build agents: {len(build)}"
    if t.startswith("The review ran in a separate fresh agent"):
        return bool(review), f"review agents: {len(review)}"
    if t.startswith("The review ran isolated"):
        _, plan = boxes(repo)
        reviewed = "## Review" in plan
        return bool(review) or (reviewed and not build), f"review agents: {len(review)}; build agents: {len(build)}; reviewed: {reviewed}"
    if t.startswith("The review agent's prompt holds no build report"):
        if not review:
            return False, "no review agent"
        p = review[-1][0]
        leak = BUILD_REPORT.search(p)
        return len(p) < 2500 and not leak, f"{len(p)} chars; leak: {leak.group(0) if leak else None}"
    if t.startswith("The plan has a ## Review"):
        _, plan = boxes(repo)
        return bool(re.search(r"^## Review", plan, re.M)), "found" if "## Review" in plan else "absent"
    if t.startswith("Tagging a bookmark twice"):
        tags = stored_tags(repo)
        return tags == ["work"], f"stored tags: {tags}"
    if t == "npm test passes":
        r = sh(repo, "npm", "test")
        return r.returncode == 0, (r.stdout + r.stderr).strip().splitlines()[-1][:80] if (r.stdout + r.stderr).strip() else ""
    if t.startswith("Nothing was pushed"):
        heads = sh(ctx["fx"] / "origin.git", "git", "for-each-ref", "--format=%(refname:short)", "refs/heads").stdout.split()
        calls = (ctx["fx"] / "calls.jsonl").read_text()
        created = '"create"' in calls
        return heads == ["main"] and not created, f"remote heads: {heads}; mr create: {created}"
    if t.startswith("Response drafts the MR"):
        r = ctx["response"]
        ok = re.search(r"merge request|\bMR\b|push", r, re.I) or re.search(r"open|decid|recommend", r, re.I)
        return bool(ok), r.strip()[:120].replace("\n", " ")
    raise ValueError(t)


def main(it):
    it = Path(it)
    for meta in sorted(it.glob("eval-*/eval_metadata.json")):
        spec = json.loads(meta.read_text())
        for run in sorted(meta.parent.glob("*/run-*")):
            fx = (run / "fixture").resolve()
            reports = flow_reports(fx)
            exps = spec["assertions"] + (spec.get("flow_assertions", []) if reports is not None else [])
            timing = json.loads((run / "timing.json").read_text()) if (run / "timing.json").exists() else {}
            ctx = {"run": run, "fx": fx, "repo": fx / "repo",
                   "branch_sha": (run / "branch_sha").read_text().strip(),
                   "calls": agent_calls(timing.get("session_id")),
                   "response": (run / "outputs/response.md").read_text() if (run / "outputs/response.md").exists() else ""}
            results = []
            for t in exps:
                ok, ev = check(t, ctx) if t in spec["assertions"] else flow_check(t, reports or [], boxes(ctx["repo"])[1])
                results.append({"text": t, "passed": bool(ok), "evidence": ev})
            n = sum(r["passed"] for r in results)
            (run / "grading.json").write_text(json.dumps({"expectations": results, "summary": {
                "passed": n, "failed": len(results) - n, "total": len(results),
                "pass_rate": round(n / len(results), 3)}}, indent=2))
            log = git(ctx["repo"], "log", "--format=%h %s", f"{ctx['branch_sha']}..HEAD")
            agents = "\n".join(f"- {d}: {len(p)} chars" for p, d in ctx["calls"])
            flow = "\n".join(" ".join(r) for r in reports) if reports is not None else "(ran without flow)"
            (run / "outputs/flow_result.txt").write_text(f"new commits:\n{log}\nagents:\n{agents}\nflow reports:\n{flow}\n")
            print(f"{run.relative_to(it)}: {n}/{len(results)}")


if __name__ == "__main__":
    main(sys.argv[1])
