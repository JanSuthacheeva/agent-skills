#!/usr/bin/env python3
"""Grade ship-feature eval runs from each run's repository, the forge stub
log, the bare remote and the session transcript (for which steps ran in a
fresh agent and what that agent was told).

Usage: grade.py <iteration-dir>
Writes <run>/grading.json and <run>/outputs/flow_result.txt for every run.
"""
import json, os, re, subprocess, sys, tempfile
from pathlib import Path

PLAN = "docs/plans/2026-10-14-bookmark-tags.md"
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


def stored_tags(repo):
    with tempfile.TemporaryDirectory() as tmp:
        file = Path(tmp) / "store"
        env = {**os.environ, "BM_FILE": str(file)}
        sh(repo, "node", "src/main.ts", "add", "https://a.dev", "A", env=env)
        sh(repo, "node", "src/main.ts", "tag", "1", "work", env=env)
        sh(repo, "node", "src/main.ts", "tag", "1", "work", env=env)
        return json.loads(file.read_text())[0].get("tags") if file.exists() else None


def check(t, ctx):
    repo, run = ctx["repo"], ctx["run"]
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
    if t == "The build ran in this session, not in an agent":
        b, _ = boxes(repo)
        return not build and b == ["x"] * 5, f"build agents: {len(build)}; boxes: {''.join(b)}"
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
        exps = json.loads(meta.read_text())["assertions"]
        for run in sorted(meta.parent.glob("*/run-*")):
            fx = (run / "fixture").resolve()
            timing = json.loads((run / "timing.json").read_text()) if (run / "timing.json").exists() else {}
            ctx = {"run": run, "fx": fx, "repo": fx / "repo",
                   "branch_sha": (run / "branch_sha").read_text().strip(),
                   "calls": agent_calls(timing.get("session_id")),
                   "response": (run / "outputs/response.md").read_text() if (run / "outputs/response.md").exists() else ""}
            results = []
            for t in exps:
                ok, ev = check(t, ctx)
                results.append({"text": t, "passed": bool(ok), "evidence": ev})
            n = sum(r["passed"] for r in results)
            (run / "grading.json").write_text(json.dumps({"expectations": results, "summary": {
                "passed": n, "failed": len(results) - n, "total": len(results),
                "pass_rate": round(n / len(results), 3)}}, indent=2))
            log = git(ctx["repo"], "log", "--format=%h %s", f"{ctx['branch_sha']}..HEAD")
            agents = "\n".join(f"- {d}: {len(p)} chars" for p, d in ctx["calls"])
            (run / "outputs/flow_result.txt").write_text(f"new commits:\n{log}\nagents:\n{agents}\n")
            print(f"{run.relative_to(it)}: {n}/{len(results)}")


if __name__ == "__main__":
    main(sys.argv[1])
