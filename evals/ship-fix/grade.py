#!/usr/bin/env python3
"""Grade ship-fix eval runs from each run's repository, the forge stub log,
the bare remote and the session transcript (for which steps ran in a fresh
agent and what that agent was told).

Usage: grade.py <iteration-dir>
Writes <run>/grading.json and <run>/outputs/flow_result.txt for every run.
"""
import json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

PLAN = "docs/plans/2026-10-27-fix-tags-lost.md"
BUILD_REPORT = re.compile(r"deviation|I (built|implemented|fixed)|has been (built|implemented|fixed)|tasks? \d+ (to|-) \d+ (are|were) (done|built)", re.I)
APPROVAL = re.compile(r"approv|go ahead|shall I|should I (start|build|proceed)|ok to (build|proceed)|sign.?off|confirm", re.I)


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


def changed(repo, base, *paths):
    """Files under paths that differ from base, committed or not, tracked or new."""
    diff = git(repo, "diff", "--name-only", base, "--", *paths).split()
    new = git(repo, "ls-files", "--others", "--exclude-standard", "--", *paths).split()
    return sorted(set(diff + new))


def fix_plans(repo, base):
    found = []
    for f in changed(repo, base, "."):
        p = repo / f
        if f.endswith(".md") and p.is_file() and re.search(r"^#+ Root cause", p.read_text(), re.I | re.M):
            found.append((f, p.read_text()))
    return found


def tags_survive_add(repo):
    with tempfile.TemporaryDirectory() as tmp:
        env = {**os.environ, "BM_FILE": str(Path(tmp) / "bm.json")}
        for args in (["add", "https://a.dev", "A"], ["tag", "1", "work"], ["add", "https://b.dev", "B"]):
            sh(repo, "node", "src/main.ts", *args, env=env)
        return sh(repo, "node", "src/main.ts", "list", "--tag", "work", env=env).stdout.strip()


def fails_on_base(repo, base, tests):
    failing = []
    with tempfile.TemporaryDirectory() as tmp:
        sh(repo, "git", "worktree", "add", "-q", "--detach", tmp, base)
        try:
            for t in tests:
                shutil.copy(repo / t, Path(tmp) / t)
                if sh(tmp, "node", "--test", t).returncode != 0:
                    failing.append(t)
        finally:
            sh(repo, "git", "worktree", "remove", "--force", tmp)
    return failing


def check(t, ctx):
    repo, base = ctx["repo"], ctx["branch_sha"]
    build = [c for c in ctx["calls"] if re.search(r"implement-plan", c[0]) or re.search(r"\bbuild", c[1], re.I)]
    review = [c for c in ctx["calls"] if re.search(r"review-changes", c[0])]
    plan = (repo / PLAN).read_text() if (repo / PLAN).exists() else ""
    if t.startswith("A fix plan names"):
        plans = fix_plans(repo, base)
        named = [f for f, p in plans if re.search(r"toRecord", p) and "store.ts" in p]
        return bool(named), f"plans: {[f for f, _ in plans]}; naming toRecord: {named}"
    if t == "src/ and test/ are unchanged":
        dirty = changed(repo, base, "src", "test")
        return not dirty, f"changed: {dirty}"
    if t == "Nothing was committed to main":
        main = git(repo, "rev-parse", "main").strip()
        return main == base, f"main: {main[:7]}, was {base[:7]}"
    if t.startswith("Nothing was pushed"):
        heads = sh(ctx["fx"] / "origin.git", "git", "for-each-ref", "--format=%(refname:short)", "refs/heads").stdout.split()
        created = '"create"' in (ctx["fx"] / "calls.jsonl").read_text()
        return heads == ["main"] and not created, f"remote heads: {heads}; mr create: {created}"
    if t.startswith("Response asks the user to approve"):
        m = APPROVAL.search(ctx["response"])
        return bool(m), m.group(0) if m else ctx["response"].strip()[:120].replace("\n", " ")
    if t == "All plan boxes are ticked":
        boxes = re.findall(r"^- \[([ x])\]", plan, re.M)
        return bool(boxes) and all(b == "x" for b in boxes), "".join(boxes)
    if t == "The build ran in this session, not in an agent":
        return not build, f"build agents: {len(build)}"
    if t.startswith("A regression test fails on the pre-fix source"):
        tests = [f for f in changed(repo, base, "test") if f.endswith(".test.ts")]
        failing = fails_on_base(repo, base, tests) if tests else []
        return bool(failing), f"changed tests: {tests}; fail before the fix: {failing}"
    if t.startswith("Tags survive bm add"):
        listed = tags_survive_add(repo)
        return listed.startswith("1  A"), f"list --tag work after add: {listed!r}"
    if t.startswith("The review ran in a separate fresh agent"):
        return bool(review), f"review agents: {len(review)}"
    if t.startswith("The review agent's prompt holds no build report"):
        if not review:
            return False, "no review agent"
        p = review[-1][0]
        leak = BUILD_REPORT.search(p)
        return len(p) < 2500 and not leak, f"{len(p)} chars; leak: {leak.group(0) if leak else None}"
    if t.startswith("The plan has a ## Review"):
        return bool(re.search(r"^## Review", plan, re.M)), "found" if "## Review" in plan else "absent"
    if t == "npm test passes":
        r = sh(repo, "npm", "test")
        out = (r.stdout + r.stderr).strip()
        return r.returncode == 0, out.splitlines()[-1][:80] if out else ""
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
            timing = json.loads((run / "timing.json").read_text()) if (run / "timing.json").exists() else {}
            ctx = {"fx": fx, "repo": fx / "repo", "branch_sha": (run / "branch_sha").read_text().strip(),
                   "calls": agent_calls(timing.get("session_id")),
                   "response": (run / "outputs/response.md").read_text() if (run / "outputs/response.md").exists() else ""}
            results = []
            for t in spec["assertions"]:
                ok, ev = check(t, ctx)
                results.append({"text": t, "passed": bool(ok), "evidence": ev})
            n = sum(r["passed"] for r in results)
            (run / "grading.json").write_text(json.dumps({"expectations": results, "summary": {
                "passed": n, "failed": len(results) - n, "total": len(results),
                "pass_rate": round(n / len(results), 3)}}, indent=2))
            log = git(ctx["repo"], "log", "--all", "--format=%h %D %s", f"^{ctx['branch_sha']}")
            status = git(ctx["repo"], "status", "--short")
            agents = "\n".join(f"- {d}: {len(p)} chars" for p, d in ctx["calls"])
            (run / "outputs/flow_result.txt").write_text(f"new commits:\n{log}\nstatus:\n{status}\nagents:\n{agents}\n")
            print(f"{run.relative_to(it)}: {n}/{len(results)}")


if __name__ == "__main__":
    main(sys.argv[1])
