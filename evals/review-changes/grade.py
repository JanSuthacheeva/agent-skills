#!/usr/bin/env python3
"""Grade review-changes eval runs by probing each run's repo: the CLI and
store behaviour behind each planted defect, the plan, the tests and the
commits made on top of the branch.

Usage: grade.py <iteration-dir>
Writes <run>/grading.json and <run>/outputs/review_result.txt for every run.
"""
import json, os, re, subprocess, sys, tempfile
from pathlib import Path

PLAN = "docs/plans/2026-10-14-bookmark-tags.md"
PROBLEMS = {
    "duplicate tags": r"duplicat|twice|already ha",
    "list --tag not normalized": r"normali[sz]|case|uppercase|Work",
    "unknown id exit code": r"exit (code )?1|exits? 1|exit code",
    "listTagged vs listByTag": r"listByTag|listTagged",
    "missing unknown-id test": r"\btest",
}


def sh(cwd, *args, env=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=env, timeout=300)


def git(repo, *args):
    return sh(repo, "git", *args).stdout


def bm(repo, file, *args):
    result = sh(repo, "node", "src/main.ts", *args, env={**os.environ, "BM_FILE": str(file)})
    return result.returncode, result.stdout + result.stderr


def stored_tags(repo):
    with tempfile.TemporaryDirectory() as tmp:
        file = Path(tmp) / "store"
        bm(repo, file, "add", "https://a.dev", "A")
        bm(repo, file, "tag", "1", "work")
        bm(repo, file, "tag", "1", "work")
        return json.loads(file.read_text())[0].get("tags") if file.exists() else None


def check(t, repo, branch, new, response):
    if t.startswith("Tagging a bookmark twice"):
        tags = stored_tags(repo)
        return tags == ["work"], f"stored tags: {tags}"
    if t.startswith("list --tag Work"):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "store"
            bm(repo, file, "add", "https://a.dev", "A")
            bm(repo, file, "tag", "1", "work")
            code, out = bm(repo, file, "list", "--tag", "Work")
            return code == 0 and "a.dev" in out, f"exit {code}: {out.strip()[:80]}"
    if t.startswith("Tagging an unknown id"):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "store"
            bm(repo, file, "add", "https://a.dev", "A")
            code, out = bm(repo, file, "tag", "9", "work")
            return code == 1, f"exit {code}: {out.strip()[:80]}"
    if t.startswith("The store's filter method"):
        store = (repo / "src/store.ts").read_text()
        plan = (repo / PLAN).read_text()
        in_store = set(re.findall(r"\b(listByTag|listTagged)\(", store))
        in_plan = set(re.findall(r"\b(listByTag|listTagged)\b", plan))
        return len(in_store) == 1 and in_store == in_plan, f"store: {sorted(in_store)}, plan: {sorted(in_plan)}"
    if t.startswith("A test covers tagging an unknown id"):
        hits = [f for f in git(repo, "ls-files", "test").split()
                if re.search(r"BookmarkNotFoundError|no bookmark", (repo / f).read_text())]
        return bool(hits), f"test files: {hits}"
    if t.startswith("The CLI tags through BookmarkStore::tag"):
        cli = (repo / "src/cli.ts").read_text()
        ok = "store.tag(" in cli and "store.save(" not in cli
        return ok, f"store.tag( in cli: {'store.tag(' in cli}; store.save( in cli: {'store.save(' in cli}"
    if t.startswith("A corrupt store file is not overwritten"):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "store"
            corrupt = '[{"id": 1, "url": "https://a.dev",'
            file.write_text(corrupt)
            code, out = bm(repo, file, "add", "https://x.dev", "X")
            kept = file.read_text() == corrupt
            return kept, f"add exit {code}, file kept: {kept}: {out.strip()[:60]}"
    if t.startswith("src/store.ts prints nothing"):
        hits = re.findall(r"console\.\w+", (repo / "src/store.ts").read_text())
        return not hits, f"console calls: {hits}"
    if t.startswith("npm test passes"):
        result = sh(repo, "npm", "test")
        return result.returncode == 0, (result.stdout + result.stderr)[-200:]
    if t.startswith("src/tags.ts is unchanged"):
        diff = git(repo, "diff", branch, "--", "src/tags.ts")
        return not diff, f"{len(diff.splitlines())} diff lines"
    if t.startswith("The fixes are committed"):
        status = git(repo, "status", "--short")
        return bool(new) and not status.strip(), f"{len(new)} new commit(s); status: {status.strip() or 'clean'}"
    if t.startswith("Response names at least four"):
        named = [p for p, rx in PROBLEMS.items() if re.search(rx, response, re.I)]
        return len(named) >= 4, f"named: {named} (keyword heuristic, verify manually)"
    raise ValueError(t)


it = Path(sys.argv[1])
for meta_path in sorted(it.glob("*/eval_metadata.json")):
    meta = json.loads(meta_path.read_text())
    for run in sorted(meta_path.parent.glob("*/run-*")):
        repo = (run / "repo").resolve()
        branch = (run / "branch_sha").read_text().strip()
        new = git(repo, "rev-list", "--reverse", f"{branch}..HEAD").split()
        resp_path = run / "outputs" / "response.md"
        response = resp_path.read_text() if resp_path.exists() else ""
        exps = []
        for a in meta["assertions"]:
            ok, ev = check(a, repo, branch, new, response)
            exps.append({"text": a, "passed": bool(ok), "evidence": ev})
        (run / "outputs" / "review_result.txt").write_text(
            f"New commits: {len(new)}\n" + git(repo, "log", "--stat", "--format=%n%h %s%n%b", f"{branch}..HEAD")
            + "\n--- git status --short ---\n" + git(repo, "status", "--short") + "\n")
        p = sum(e["passed"] for e in exps)
        (run / "grading.json").write_text(json.dumps({"expectations": exps,
            "summary": {"passed": p, "failed": len(exps) - p, "total": len(exps), "pass_rate": round(p / len(exps), 2)}}, indent=2))
        print(f"{meta['eval_name']:16} {run.parent.name:14} {run.name} {p}/{len(exps)}")
