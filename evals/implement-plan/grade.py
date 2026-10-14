#!/usr/bin/env python3
"""Grade implement-plan eval runs by inspecting each run's repo: commits,
the plan's checkboxes, the code, and the CLI run end to end.

Usage: grade.py <iteration-dir>
Writes <run>/grading.json and <run>/outputs/build_result.txt for every run.
"""
import json, os, re, subprocess, sys, tempfile
from pathlib import Path

PLAN = "docs/plans/2026-10-14-bookmark-tags.md"
CSV_HEADER = "id,url,title,createdAt"


def sh(cwd, *args, env=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=env, timeout=300)


def git(repo, *args):
    return sh(repo, "git", *args).stdout


def tests_pass(repo):
    result = sh(repo, "npm", "test")
    return result.returncode == 0, (result.stdout + result.stderr)[-400:]


def green_commits(repo, shas):
    """Run npm test at every new commit in a scratch worktree."""
    red = []
    with tempfile.TemporaryDirectory() as tmp:
        tree = Path(tmp) / "tree"
        sh(repo, "git", "worktree", "add", "-q", "--detach", str(tree), shas[0] if shas else "HEAD")
        for sha in shas:
            sh(tree, "git", "checkout", "-q", "--detach", sha)
            if sh(tree, "npm", "test").returncode != 0:
                red.append(sha[:7])
        sh(repo, "git", "worktree", "remove", "--force", str(tree))
    return red


def boxes(repo):
    text = (repo / PLAN).read_text() if (repo / PLAN).exists() else ""
    tasks = text.split("## Tasks", 1)[1] if "## Tasks" in text else ""
    return [m == "x" for m in re.findall(r"^- \[([ xX])\]", tasks, re.M)]


def bm(repo, file, *args):
    env = {**os.environ, "BM_FILE": str(file)}
    result = sh(repo, "node", "src/main.ts", *args, env=env)
    return result.returncode, result.stdout + result.stderr


def end_to_end(repo):
    with tempfile.TemporaryDirectory() as tmp:
        file = Path(tmp) / "store"
        steps = [bm(repo, file, "add", "https://a.dev", "A"), bm(repo, file, "add", "https://b.dev", "B"),
                 bm(repo, file, "tag", "1", " Work ")]
        code, listed = bm(repo, file, "list", "--tag", "work")
        ok = all(c == 0 for c, _ in steps) and code == 0 and "a.dev" in listed and "b.dev" not in listed
        return ok, f"list --tag work -> {code}: {listed.strip()[:120]}"


def old_file_loads(repo):
    with tempfile.TemporaryDirectory() as tmp:
        file = Path(tmp) / "store"
        file.write_text(json.dumps([{"id": 1, "url": "https://a.dev", "title": "A", "createdAt": "2026-01-01T00:00:00.000Z"}]))
        code, out = bm(repo, file, "list")
        return code == 0 and "a.dev" in out, f"list -> {code}: {out.strip()[:120]}"


def check(t, repo, base, new, response):
    ticked = boxes(repo)
    head = lambda path: git(repo, "show", f"HEAD:{path}")
    if t.startswith("Five new commits"):
        return len(new) == 5, f"{len(new)} new commit(s)"
    if t.startswith("Every new commit leaves npm test passing"):
        red = green_commits(repo, new)
        return bool(new) and not red, f"red commits: {red or 'none'} of {len(new)}"
    if t.startswith("All five task checkboxes"):
        return len(ticked) == 5 and all(ticked), f"ticked: {ticked}"
    if t.startswith("src/tags.ts exports"):
        src = head("src/tags.ts")
        ok = bool(re.search(r"export function normalizeTag\(\s*raw: string\s*\): string", src)) and \
            bool(re.search(r"export class InvalidTagError extends Error", src))
        return ok, "signature regex on src/tags.ts"
    if t.startswith("BookmarkStore has tag"):
        src = head("src/store.ts")
        ok = bool(re.search(r"\btag\(\s*id: number,\s*tag: string\s*\): Bookmark\b", src)) and \
            bool(re.search(r"\blistByTag\(\s*tag: string\s*\): Bookmark\[\]", src))
        return ok, "signature regex on src/store.ts"
    if t.startswith("A test file covers normalizeTag"):
        files = git(repo, "ls-files", "test").split()
        hit = [f for f in files if "normalizeTag" in head(f)]
        return bool(hit), f"test files: {hit}"
    if t.startswith("The CLI tags a bookmark"):
        return end_to_end(repo)
    if t.startswith("A file written before tags"):
        return old_file_loads(repo)
    if t.startswith("The working tree is clean"):
        status = git(repo, "status", "--short")
        return not status.strip(), status.strip() or "clean"
    if t.startswith("Task 1 is ticked"):
        return bool(ticked) and ticked[0] and bool(head("src/tags.ts")), f"ticked: {ticked}"
    if t.startswith("Tasks 2 to 5 are not ticked"):
        return len(ticked) == 5 and not any(ticked[1:]), f"ticked: {ticked}"
    if t.startswith("The stored CSV format is unchanged"):
        store = (repo / "src/store.ts").read_text()
        ok = f"const header = '{CSV_HEADER}'" in store and "tags" not in store
        return ok, "header line and no tags in working-tree src/store.ts"
    if t.startswith("src/cli.ts is unchanged"):
        diff = git(repo, "diff", base, "--", "src/cli.ts")
        return not diff, f"{len(diff.splitlines())} diff lines"
    if t.startswith("Response asks how tags should be stored"):
        r = response.lower()
        ok = "?" in response and "csv" in r and bool(re.search(r"column|format|store|stored", r))
        return ok, "keywords ? + csv + column/format/store in response.md (verify manually)"
    if t.startswith("npm test passes"):
        return tests_pass(repo)
    raise ValueError(t)


it = Path(sys.argv[1])
for meta_path in sorted(it.glob("*/eval_metadata.json")):
    meta = json.loads(meta_path.read_text())
    for run in sorted(meta_path.parent.glob("*/run-*")):
        repo = (run / "repo").resolve()
        base = (run / "base_sha").read_text().strip()
        new = git(repo, "rev-list", "--reverse", f"{base}..HEAD").split()
        resp_path = run / "outputs" / "response.md"
        response = resp_path.read_text() if resp_path.exists() else ""
        exps = []
        for a in meta["assertions"]:
            ok, ev = check(a, repo, base, new, response)
            exps.append({"text": a, "passed": bool(ok), "evidence": ev})
        (run / "outputs" / "build_result.txt").write_text(
            f"New commits: {len(new)}\n" + git(repo, "log", "--stat", "--format=%n%h %s%n%b", f"{base}..HEAD")
            + "\n--- git status --short ---\n" + git(repo, "status", "--short")
            + "\n--- plan tasks ---\n" + str(boxes(repo)) + "\n")
        p = sum(e["passed"] for e in exps)
        (run / "grading.json").write_text(json.dumps({"expectations": exps,
            "summary": {"passed": p, "failed": len(exps) - p, "total": len(exps), "pass_rate": round(p / len(exps), 2)}}, indent=2))
        print(f"{meta['eval_name']:10} {run.parent.name:14} {run.name} {p}/{len(exps)}")
