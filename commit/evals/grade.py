#!/usr/bin/env python3
"""Grade commit-skill eval runs by inspecting each run's repo.

Usage: grade.py <iteration-dir>
Writes <run>/grading.json and <run>/outputs/git_result.txt for every run.
"""
import json, re, subprocess, sys
from pathlib import Path

TYPE_RE = re.compile(r"^(feat|fix|chore|docs|refactor|test|perf|style|build|ci)(\(.+\))?!?:", re.I)

def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True).stdout

def subject_ok(subj):
    m = re.match(r"^([^:]+(?:: [^:]+)*?): (.+)$", subj)
    desc = subj.split(": ")[-1] if ": " in subj else subj
    return len(subj) <= 72 and desc[:1] == desc[:1].lower() and not subj.endswith(".")

def check(text, msg, subj, body, n_new, pushed, staged, response, repo):
    t = text
    if t.startswith("Exactly one new commit"): return n_new == 1, f"{n_new} new commit(s)"
    if t.startswith("No new commit"): return n_new == 0, f"{n_new} new commit(s)"
    if t.startswith("Subject starts with"):
        return n_new > 0 and subj.startswith(re.search(r"`(.+?)`", t).group(1)), subj
    if t.startswith("HEAD is a revert"):
        return subj == 'Revert "worker: retry failed exports"' and "This reverts commit" in msg, subj
    if t.startswith("HEAD is a merge commit"):
        parents = len(git(repo, "rev-list", "--parents", "-n1", "HEAD").split()) - 1
        return parents == 2 and subj.startswith("Merge branch 'feature/"), f"{parents} parents: {subj}"
    if t.startswith("Unrelated worker/export.py"):
        st = git(repo, "status", "--short", "worker/export.py")
        return st.startswith(" M") and "worker/export.py" not in git_committed_files, f"status: {st.strip() or 'clean'}"
    if t.startswith("Response mentions the left-out worker"):
        return "worker/export.py" in response, "keyword check on response.md"
    if t.startswith("Subject scope covers both"):
        scope = subj.split(":")[0]
        return "api" in scope and "worker" in scope, subj
    if t.startswith("Subject has no conventional type"): return n_new > 0 and not TYPE_RE.match(subj), subj
    if t.startswith("Subject is <=72"): return n_new > 0 and subject_ok(subj), f"{len(subj)} chars: {subj}"
    if t.startswith("Message contains the trailer"):
        want = re.search(r"`(.+)`", t).group(1)
        return any(l.strip() == want for l in msg.splitlines()), msg.splitlines()[-1] if msg else "no commit"
    if t.startswith("Message has no Co-Authored"): return n_new > 0 and "co-authored-by" not in msg.lower(), "checked message"
    if t.startswith("Message has no Refs"): return n_new > 0 and "refs:" not in msg.lower(), msg.splitlines()[-1] if msg else "no commit"
    if t.startswith("Nothing was pushed"): return not pushed, "origin refs: " + (", ".join(pushed) or "unchanged")
    if t.startswith("Scratch files"):
        bad = [f for f in ("debug_dump.txt", "notes.md") if f in staged or f in git_committed_files]
        return not bad, f"staged: {staged or 'none'}; committed scratch: {bad or 'none'}"
    if t.startswith("Commit contains exactly"):
        want = sorted(re.findall(r"\w+/\w+\.py", t))
        return n_new == 1 and sorted(git_committed_files) == want, f"committed: {git_committed_files}"
    if t.startswith("Response names the left-out"):
        return "debug_dump.txt" in response and "notes.md" in response, "keyword check on response.md"
    if t.startswith("Response proposes"):
        return "worker/export.py" in response and "worker/test_export.py" in response, "keyword check on response.md"
    if t.startswith("Response tells the user it did not push"):
        r = response.lower()
        return not pushed and bool(re.search(r"(did not|didn't|not|won't|will not|haven't|skipp)\w*\s[^.]{0,40}push|push[^.]{0,40}(yourself|manually)", r)), "regex on response.md (verify manually)"
    if t.startswith("Body states the breaking"):
        b = body.lower(); return "currency" in b and bool(re.search(r"remov|drop|breaking", b)), "keyword check on body (verify manually)"
    if t.startswith("Body gives the client migration"):
        b = body.lower(); return bool(re.search(r"client|caller|consumer", b)) and bool(re.search(r"drop|stop send|remove|read|response", b)), "keyword check on body (verify manually)"
    if t.startswith("Body lines wrapped"):
        long = [l for l in body.splitlines() if len(l) > 72]
        return bool(body.strip()) and not long, f"longest {max((len(l) for l in body.splitlines()), default=0)}"
    raise ValueError(t)

it = Path(sys.argv[1])
for meta_path in sorted(it.glob("*/eval_metadata.json")):
    meta = json.loads(meta_path.read_text())
    for run in sorted(meta_path.parent.glob("*/run-*")):
        repo = run / "repo"
        base_file = run / "base_sha"
        base = base_file.read_text().strip() if base_file.exists() else git(repo, "log", "--format=%H", "-1", "--grep=^treewide: bump python").strip()
        new = git(repo, "rev-list", f"{base}..HEAD").split()
        msg = git(repo, "log", "-1", "--format=%B").strip() if new else ""
        subj = msg.splitlines()[0] if msg else ""
        body = "\n".join(l for l in msg.splitlines()[1:] if not re.match(r"^(Refs|Co-Authored-By):", l, re.I)).strip()
        refs = git(run / "origin.git", "for-each-ref", "--format=%(refname) %(objectname)").splitlines()
        pushed = [r for r in refs if r != f"refs/heads/main {base}"]
        staged = git(repo, "diff", "--staged", "--name-only").split()
        git_committed_files = git(repo, "diff", "--name-only", base, "HEAD").split() if new else []
        resp_path = run / "outputs" / "response.md"
        response = resp_path.read_text() if resp_path.exists() else ""
        exps = []
        for a in meta["assertions"]:
            ok, ev = check(a, msg, subj, body, len(new), pushed, staged, response, repo)
            exps.append({"text": a, "passed": bool(ok), "evidence": ev})
        (run / "outputs" / "git_result.txt").write_text(
            f"New commits: {len(new)}\n\n"
            + (git(repo, "log", "-p", f"{base}..HEAD") if new else "(none)\n")
            + "\n--- git status --short ---\n" + git(repo, "status", "--short")
            + "\n--- origin refs ---\n" + "\n".join(refs) + "\n")
        p = sum(e["passed"] for e in exps)
        (run / "grading.json").write_text(json.dumps({"expectations": exps,
            "summary": {"passed": p, "failed": len(exps) - p, "total": len(exps), "pass_rate": round(p / len(exps), 2)}}, indent=2))
        print(f"{meta["eval_name"]:22} {run.parent.name:14} {p}/{len(exps)}  {subj}")
