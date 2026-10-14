#!/usr/bin/env python3
"""Grade write-merge-request eval runs from each run's response, repo, origin and
stub call log.

Usage: grade.py <iteration-dir>
Writes <run>/grading.json and <run>/outputs/mr_result.txt for every run.
Text checks are keyword heuristics; the evidence says what was matched, so
borderline passes can be verified by hand.
"""
import json, re, subprocess, sys
from pathlib import Path

TEST_HEADING = re.compile(r"^\s*(#+\s*|\*\*)?(how to test|testing|test plan|tests)\b", re.I | re.M)
TICKET_FILES = ("billing/export.py", "api/export.py", "billing/test_export.py")


def quoted(t):
    m = re.search(r"`(.+?)`", t)
    if m is None:
        raise ValueError(f"no quoted value in {t!r}")
    return m.group(1)


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True).stdout


def drafted(response):
    """The drafted MR: the fenced blocks when there are any, else the reply."""
    blocks = re.findall(r"```[^\n]*\n(.*?)```", response, re.S)
    return "\n".join(blocks) if blocks else response


def created(calls):
    return [c for c in calls
            if c[:3] in (["glab", "mr", "create"], ["gh", "pr", "create"]) and "--help" not in c and "-h" not in c]


def final_description(calls):
    """The MR description as it ended up: from the create call, or from a
    later update that replaced it."""
    desc = ""
    for c in calls:
        if c[:3] in (["glab", "mr", "create"], ["gh", "pr", "create"], ["glab", "mr", "update"], ["gh", "pr", "edit"]):
            names = ("--description", "-d") if c[0] == "glab" else ("--body", "-b")
            desc = flag(c, *names) or desc
    return desc


def flag(call, *names):
    for i, arg in enumerate(call):
        for n in names:
            if arg == n and i + 1 < len(call):
                return call[i + 1]
            if arg.startswith(n + "="):
                return arg.split("=", 1)[1]
    return None


def check(t, response, draft, calls, pushed, head, repo):
    mrs = created(calls)
    mr = mrs[0] if mrs else []
    title = flag(mr, "--title", "-t") or ""
    desc = final_description(calls)
    if t.startswith("Response contains the title"):
        want = quoted(t)
        return want in response, "substring check on response.md"
    if t.startswith("Description explains why rows are streamed"):
        return bool(re.search(r"memory|stream", draft, re.I)), "keyword memory/stream in draft"
    if t.startswith("Description explains why semicolons"):
        return "excel" in draft.lower(), "keyword excel in draft"
    if t.startswith("Description explains the one-cent drift"):
        return bool(re.search(r"cent|drift|pdf", draft, re.I)), "keyword cent/drift/pdf in draft"
    if t.startswith("Description uses the template headings"):
        found = [h for h in ("What", "Why", "Checklist") if re.search(rf"^#+\s*{h}\s*$", draft, re.M)]
        pos = [re.search(rf"^#+\s*{h}\s*$", draft, re.M).start() for h in found]
        return found == ["What", "Why", "Checklist"] and pos == sorted(pos), f"headings found in order: {found}"
    if t.startswith("Description does not tick Tests"):
        ticked = re.search(r"^\s*-\s*\[[xX]\]\s*Tests added", draft, re.M)
        return not ticked, "ticked" if ticked else "not ticked"
    if t.startswith("Description names the new variables"):
        want = re.findall(r"EXPORT_[A-Z_]+", t)
        missing = [v for v in want if v not in draft]
        return not missing, f"missing: {missing or 'none'}"
    if t.startswith("Description mentions the export_jobs migration"):
        return bool(re.search(r"migrat", draft, re.I)) and "export_jobs" in draft, "keywords migration + export_jobs in draft"
    if t.startswith("Description mentions the new boto3"):
        return "boto3" in draft, "keyword boto3 in draft"
    if t.startswith("Description has no How to test"):
        m = TEST_HEADING.search(draft)
        return not m, f"heading found: {m.group(0).strip()}" if m else "no test heading"
    if t.startswith("Description does not list the changed files"):
        named = [f for f in TICKET_FILES if f in draft]
        return len(named) < 3, f"files named: {named}"
    if t.startswith("Response contains `Refs:"):
        want = quoted(t)
        return want in response, "substring check on response.md"
    if t.startswith("Response contains a scoped title"):
        m = re.search(r"^[\s#>*`-]*(?:title:?\**\s*`?)?billing: \S", response, re.I | re.M)
        return bool(m), m.group(0).strip() if m else "no line starting with billing:"
    if t.startswith("Description is at most"):
        limit = int(re.findall(r"\d+", t)[0])
        return len(draft.strip()) <= limit, f"{len(draft.strip())} chars"
    if t.startswith("Response has no Refs"):
        return not re.search(r"^\s*Refs:", response, re.M), "line check on response.md"
    if t.startswith("No merge request was created"):
        return not mrs, f"create calls: {len(mrs)}"
    if t.startswith("Nothing was pushed"):
        return not pushed, "origin refs: " + (", ".join(pushed) or "unchanged")
    if t.startswith("The branch was pushed"):
        branch = git(repo, "branch", "--show-current").strip()
        hit = [r for r in pushed if r == f"refs/heads/{branch} {head}"]
        return bool(hit), "origin refs: " + (", ".join(pushed) or "unchanged")
    if t.startswith("Exactly one merge request was created with glab"):
        target = flag(mr, "--target-branch", "-b") if mrs else None
        ok = len(mrs) == 1 and mr[0] == "glab" and target in (None, "main")
        return ok, f"{len(mrs)} create call(s), target {target}"
    if t.startswith("MR title is scoped"):
        return bool(re.match(r"api: \S", title)), f"title: {title!r}"
    if t.startswith("MR description states the breaking change"):
        d = desc.lower()
        ok = bool(re.search(r"breaking|remov|drop|gone", d)) and bool(re.search(r"client|caller|consumer", d))
        return ok, "keywords breaking/removed + client in MR description"
    if t.startswith("MR description has no How to test"):
        m = TEST_HEADING.search(desc)
        return bool(mrs) and not m, f"heading found: {m.group(0).strip()}" if m else f"{len(mrs)} create call(s)"
    if t.startswith("MR description has no shell escapes"):
        return bool(mrs) and "\\`" not in desc and "\\$" not in desc, "looked for \\` and \\$ in MR description"
    if t.startswith("MR description contains"):
        want = quoted(t)
        return want in desc, "substring check on MR description"
    raise ValueError(t)


it = Path(sys.argv[1])
for meta_path in sorted(it.glob("*/eval_metadata.json")):
    meta = json.loads(meta_path.read_text())
    for run in sorted(meta_path.parent.glob("*/run-*")):
        repo = run / "repo"
        base = (run / "base_sha").read_text().strip()
        head = git(repo, "rev-parse", "HEAD").strip()
        refs = git(run / "origin.git", "for-each-ref", "--format=%(refname) %(objectname)").splitlines()
        pushed = [r for r in refs if r != f"refs/heads/main {base}"]
        log = run / "calls.jsonl"
        calls = [json.loads(l) for l in log.read_text().splitlines() if l.strip()] if log.exists() else []
        resp_path = run / "outputs" / "response.md"
        response = resp_path.read_text() if resp_path.exists() else ""
        draft = drafted(response)
        exps = []
        for a in meta["assertions"]:
            ok, ev = check(a, response, draft, calls, pushed, head, repo)
            exps.append({"text": a, "passed": bool(ok), "evidence": ev})
        (run / "outputs" / "mr_result.txt").write_text(
            "--- stub calls ---\n" + "\n".join(json.dumps(c) for c in calls)
            + "\n--- origin refs ---\n" + "\n".join(refs) + "\n")
        p = sum(e["passed"] for e in exps)
        (run / "grading.json").write_text(json.dumps({"expectations": exps,
            "summary": {"passed": p, "failed": len(exps) - p, "total": len(exps), "pass_rate": round(p / len(exps), 2)}}, indent=2))
        print(f"{meta['eval_name']:16} {run.parent.name:14} {run.name} {p}/{len(exps)}")
