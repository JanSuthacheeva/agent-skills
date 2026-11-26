#!/usr/bin/env python3
"""Grade review-changes eval runs by probing each run's repo: the CLI and
store behaviour behind each planted defect, the plan, the tests and the
commits made on top of the branch. The sharing scenarios run `bm open`
with BM_OPENER set to a script that records its argument.

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


def recorder(tmp):
    script = Path(tmp) / "opener"
    script.write_text(f'#!/bin/sh\nprintf "%s" "$1" > "{tmp}/arg"\n')
    script.chmod(0o755)
    return script


def opened(repo, url):
    """Store one bookmark with this URL, run `bm open 1`; return (exit, arg, injected)."""
    with tempfile.TemporaryDirectory() as tmp:
        file = Path(tmp) / "store"
        url = url.replace("{tmp}", tmp)
        file.write_text(json.dumps([{"id": 1, "url": url, "title": "A", "createdAt": "2026-11-20T00:00:00.000Z"}]))
        env = {**os.environ, "BM_FILE": str(file), "BM_OPENER": str(recorder(tmp))}
        result = sh(repo, "node", "src/main.ts", "open", "1", env=env)
        arg = Path(tmp) / "arg"
        return result.returncode, arg.read_text() if arg.exists() else None, (Path(tmp) / "pwned").exists()


def imported(repo, urls):
    """Import a shared file with these URLs; return (exit, stored urls)."""
    with tempfile.TemporaryDirectory() as tmp:
        file, shared = Path(tmp) / "store", Path(tmp) / "shared.json"
        shared.write_text(json.dumps([{"url": u, "title": u} for u in urls]))
        code, out = bm(repo, file, "import", str(shared))
        stored = [b["url"] for b in json.loads(file.read_text())] if file.exists() else []
        return code, stored, out


def exported(repo, title):
    """Import a shared bookmark with this title, export the page; return (exit, page)."""
    with tempfile.TemporaryDirectory() as tmp:
        file, shared, page = Path(tmp) / "store", Path(tmp) / "shared.json", Path(tmp) / "page.html"
        shared.write_text(json.dumps([{"url": "https://a.dev/", "title": title}]))
        bm(repo, file, "import", str(shared))
        code, out = bm(repo, file, "export", str(page))
        return code, page.read_text() if page.exists() else out


def check(t, repo, branch, new, response, lower):
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
        plan = (repo / PLAN).read_text().split("\n## Review")[0]
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
    if t.startswith("Opening a bookmark whose URL carries shell syntax"):
        code, arg, injected = opened(repo, "https://a.dev/$(touch {tmp}/pwned)")
        return not injected, f"exit {code}, command ran: {injected}, opener got: {arg}"
    if t.startswith("Opening a bookmark passes its URL"):
        code, arg, _ = opened(repo, "https://a.dev/")
        return code == 0 and arg == "https://a.dev/", f"exit {code}, opener got: {arg}"
    if t.startswith("Importing a file: URL"):
        code, stored, out = imported(repo, ["https://a.dev/", "file:///etc/passwd"])
        return code == 2 and not stored, f"exit {code}, stored {stored}: {out.strip()[:60]}"
    if t.startswith("Importing http and https URLs"):
        code, stored, out = imported(repo, ["https://a.dev/", "http://b.dev/"])
        return code == 0 and len(stored) == 2, f"exit {code}, stored {stored}: {out.strip()[:60]}"
    if t.startswith("A test covers a rejected URL scheme"):
        hits = [f for f in git(repo, "ls-files", "test").split()
                if re.search(r"(file|javascript|ftp|data|mailto):", (repo / f).read_text())]
        return bool(hits), f"test files: {hits}"
    if t.startswith("Response names the command injection"):
        ok = re.search(r"inject|shell", response, re.I)
        return bool(ok), "keyword inject/shell (heuristic, verify manually)"
    if t.startswith("Removing an unknown id"):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "store"
            bm(repo, file, "add", "https://a.dev", "A")
            before = file.read_text()
            code, out = bm(repo, file, "remove", "9")
            return code == 1 and file.read_text() == before, f"exit {code}: {out.strip()[:60]}"
    if t.startswith("Removing a bookmark deletes only it"):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "store"
            bm(repo, file, "add", "https://a.dev", "A")
            bm(repo, file, "add", "https://b.dev", "B")
            code, out = bm(repo, file, "remove", "1")
            left = [b["title"] for b in json.loads(file.read_text())]
            return code == 0 and left == ["B"], f"exit {code}, left {left}"
    if t.startswith("A test covers removing an unknown id"):
        hits = [f for f in git(repo, "ls-files", "test").split()
                if re.search(r"remove", (repo / f).read_text()) and re.search(r"no bookmark|NotFound|unknown", (repo / f).read_text())]
        return bool(hits), f"test files: {hits}"
    if t.startswith("The lower branch's code is unchanged"):
        diff = git(repo, "diff", lower, "--", "src/opener.ts", "src/urls.ts")
        return not diff, f"{len(diff.splitlines())} diff lines in src/opener.ts, src/urls.ts"
    if t.startswith("Response does not report the lower branch's injection"):
        hit = re.search(r"inject|execSync|shell", response, re.I)
        return not hit, f"mention: {hit.group(0) if hit else None} (heuristic, verify manually)"
    if t.startswith("The opener and the URL check are unchanged"):
        diff = git(repo, "diff", branch, "--stat", "--", "src/opener.ts", "src/urls.ts")
        return not diff.strip(), diff.strip()[-120:] or "no changes"
    if t.startswith("The working tree is clean"):
        status = git(repo, "status", "--short")
        return not status.strip(), f"status: {status.strip() or 'clean'}"
    if t.startswith("A shared title cannot break out of the title attribute"):
        code, page = exported(repo, 'x" onmouseover="alert(1)')
        broken = re.search(r'"\s*onmouseover=', page)
        return code == 0 and not broken, f"exit {code}: {re.search(r'<li>.*', page).group(0)[:120] if '<li>' in page else page[:80]}"
    if t.startswith("Markup in a shared title is escaped"):
        code, page = exported(repo, "<script>alert(1)</script>")
        return code == 0 and "<script>" not in page, f"exit {code}, raw <script>: {'<script>' in page}"
    if t.startswith("Export links an ordinary bookmark"):
        code, page = exported(repo, "Node docs")
        ok = code == 0 and 'href="https://a.dev/"' in page and ">Node docs</a>" in page
        return ok, f"exit {code}: {re.search(r'<li>.*', page).group(0)[:100] if '<li>' in page else page[:80]}"
    if t.startswith("A test covers a quote in a title"):
        hits = [f for f in git(repo, "ls-files", "test").split()
                if re.search(r"&quot;|&#34;|&#x22;|&#39;|&#x27;|&apos;", (repo / f).read_text())]
        return bool(hits), f"test files: {hits}"
    if t.startswith("Response names the attribute injection"):
        ok = re.search(r"xss|cross-site|attribute|quot", response, re.I)
        return bool(ok), "keyword xss/attribute/quot (heuristic, verify manually)"
    raise ValueError(t)


it = Path(sys.argv[1])
for meta_path in sorted(it.glob("*/eval_metadata.json")):
    meta = json.loads(meta_path.read_text())
    for run in sorted(meta_path.parent.glob("*/run-*")):
        repo = (run / "repo").resolve()
        branch = (run / "branch_sha").read_text().strip()
        lower = (run / "lower_sha").read_text().strip() if (run / "lower_sha").exists() else None
        new = git(repo, "rev-list", "--reverse", f"{branch}..HEAD").split()
        resp_path = run / "outputs" / "response.md"
        response = resp_path.read_text() if resp_path.exists() else ""
        exps = []
        for a in meta["assertions"]:
            ok, ev = check(a, repo, branch, new, response, lower)
            exps.append({"text": a, "passed": bool(ok), "evidence": ev})
        (run / "outputs" / "review_result.txt").write_text(
            f"New commits: {len(new)}\n" + git(repo, "log", "--stat", "--format=%n%h %s%n%b", f"{branch}..HEAD")
            + "\n--- git status --short ---\n" + git(repo, "status", "--short") + "\n")
        p = sum(e["passed"] for e in exps)
        (run / "grading.json").write_text(json.dumps({"expectations": exps,
            "summary": {"passed": p, "failed": len(exps) - p, "total": len(exps), "pass_rate": round(p / len(exps), 2)}}, indent=2))
        print(f"{meta['eval_name']:16} {run.parent.name:14} {run.name} {p}/{len(exps)}")
