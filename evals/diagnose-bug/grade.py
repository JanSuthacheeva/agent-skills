#!/usr/bin/env python3
"""Grade diagnose-bug eval runs from each run's repository, its reply and
the session transcripts (for the commands it ran).

Usage: grade.py <iteration-dir>
Writes <run>/grading.json and <run>/outputs/diagnosis_result.txt for every run.
Expectations starting "Diagnosis:" apply to every config; those starting
"Contract:" are what diagnose-bug promises (no code, a fix plan), graded
for every config but only expected of with_skill. Text checks are keyword
heuristics; the evidence says what was matched.
"""
import json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

PROJECTS = Path.home() / ".claude" / "projects"
CLI = re.compile(r"(src/main\.ts|npm run\b[^;&|\n]*\bbm\b)")
LOST = re.compile(
    r"(already|existing|previously|past|historic|since)\b.{0,120}\b(lost|dropp|gone|wiped|stripped|erased|removed|missing)"
    r"|(lost|dropp|wiped|stripped|erased).{0,120}\b(already|existing|users'? (data|files?)|on disk|cannot be recovered|unrecoverable)"
    r"|\b(recover|restore|backfill|repair|migrat|re-?tag)|(get|bring) them back", re.I | re.S)
NOT_REPRODUCED = re.compile(
    r"(not|n't|unable to|never|no longer)\s+(be\s+)?(reproduc|repro\b)|could not get it to|(couldn't|could not|can't|cannot) make .{0,40}happen|does not (break|corrupt)|is not reproducible"
    r"|works (correctly|fine|as expected)|handled correctly|no corruption|stays? (valid|intact)", re.I)
OLD_FILE = re.compile(
    r"before tags|pre-?tags|without (a |any )?[`\"']?tags[`\"']? (field|key|propert)|no [`\"']?tags[`\"']? (field|key|propert)"
    r"|old(er)? (bookmarks )?(file|format|version|data)|legacy|upgrad", re.I)
WRONGLY_TAGGED = re.compile(
    r"(already|existing|users'?).{0,160}\b(wrong|spurious|incorrect|extra|unwanted|bogus|polluted|bad)"
    r"|clean ?up|remove (the|those) (wrong|extra|spurious|tags)|by hand|\b(repair|migrat)|(cannot|can't|no way to) (tell|know|distinguish)", re.I | re.S)
ASKS = re.compile(r"\?|\b(share|send|attach|provide|which version|exact (steps|command)|more (detail|info)|need (the|their|a|to know)|ask (the reporter|them|for))", re.I)


def sh(cwd, *args, env=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=env, timeout=300)


def git(repo, *args):
    return sh(repo, "git", *args).stdout


def commands(sid):
    """Bash commands of the session and every subagent it started."""
    if not sid:
        return []
    files = list(PROJECTS.glob(f"*/{sid}.jsonl")) + list(PROJECTS.glob(f"*/{sid}/**/*.jsonl"))
    out = []
    for f in files:
        for line in f.read_text().splitlines():
            content = json.loads(line).get("message", {}).get("content")
            for part in content if isinstance(content, list) else []:
                if part.get("type") == "tool_use" and part.get("name") == "Bash":
                    out.append(part.get("input", {}).get("command", ""))
    return out


def changed(repo, base, *paths):
    """Files under paths that differ from base, committed or not, tracked or new."""
    diff = git(repo, "diff", "--name-only", base, "--", *paths).split()
    new = git(repo, "ls-files", "--others", "--exclude-standard", "--", *paths).split()
    return sorted(set(diff + new))


def plans(repo, base):
    """New or changed Markdown files that read like a fix plan."""
    found = []
    for f in changed(repo, base, "."):
        p = repo / f
        if f.endswith(".md") and p.is_file() and re.search(r"^#+ .*(root cause|tasks)", p.read_text(), re.I | re.M):
            found.append((f, p.read_text()))
    return found


def function(src, name):
    """The text of a method or function from its signature to its closing brace at the same indent."""
    m = re.search(rf"^(\s*)(export )?(function )?{name}\(.*?^\1}}", src, re.M | re.S)
    return m.group(0) if m else None


def tags_survive_add(repo):
    with tempfile.TemporaryDirectory() as tmp:
        env = {**os.environ, "BM_FILE": str(Path(tmp) / "bm.json")}
        for args in (["add", "https://a.dev", "A"], ["tag", "1", "work"], ["add", "https://b.dev", "B"]):
            sh(repo, "node", "src/main.ts", *args, env=env)
        return sh(repo, "node", "src/main.ts", "list", "--tag", "work", env=env).stdout.strip()


def fails_on_base(repo, base, tests):
    """Run the changed test files against the base commit's source; which fail."""
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


def spread_stopped(repo):
    """Tag one bookmark of a file written before tags; only it should carry the tag."""
    old = [{"id": i, "url": f"https://{i}.dev", "title": str(i), "createdAt": "2026-01-01T00:00:00.000Z"} for i in (1, 2, 3)]
    with tempfile.TemporaryDirectory() as tmp:
        file = Path(tmp) / "bm.json"
        file.write_text(json.dumps(old))
        env = {**os.environ, "BM_FILE": str(file)}
        sh(repo, "node", "src/main.ts", "tag", "3", "recipes", env=env)
        return sh(repo, "node", "src/main.ts", "list", "--tag", "recipes", env=env).stdout.strip()


def tasks(plan):
    m = re.search(r"^#+ Tasks\s*$(.*?)(?=^#+ |\Z)", plan, re.M | re.S | re.I)
    return re.findall(r"^\s*- \[[ x]\] (.+(?:\n(?!\s*- \[)\s+\S.*)*)", m.group(1), re.M) if m else []


def check(t, ctx):
    repo, base, reply = ctx["repo"], ctx["base"], ctx["response"]
    texts = reply + "\n".join(p for _, p in ctx["plans"])
    cli = [c for c in ctx["commands"] if CLI.search(c)]
    src = changed(repo, base, "src")
    tests = [f for f in changed(repo, base, "test") if f.endswith(".test.ts")]
    committed = git(repo, "rev-list", f"{base}..HEAD").split()
    if t.endswith("reproduced through the CLI"):
        ok = any(re.search(r"\btag\b", c) for c in cli) and any(re.search(r"\badd\b", c) for c in cli)
        return ok, f"{len(cli)} CLI commands"
    if t.endswith("with a file from before tags"):
        tagged = [c for c in cli if re.search(r"\btag\b", c)]
        m = OLD_FILE.search(texts)
        return bool(tagged and m), f"{len(tagged)} CLI tag commands; old data: {m.group(0) if m else None}"
    if t.startswith("Diagnosis: the cause named is the shared"):
        m = re.search(r"noTags|shar(ed|es|ing) (one |a |the )?(same |single )?(empty )?(`?\[\]`? )?array|same (empty )?(array|list)|one (shared )?list|shared (with|list|default)|alias", texts, re.I)
        return bool(m), m.group(0) if m else "shared array not named"
    if t.startswith("Diagnosis: any source change is in fromRecord"):
        if not src:
            return True, "no source change"
        before = git(repo, "show", f"{base}:src/store.ts")
        after = (repo / "src/store.ts").read_text() if (repo / "src/store.ts").exists() else ""
        at_cause = function(before, "fromRecord") != function(after, "fromRecord") or "noTags" not in after
        listed = spread_stopped(repo)
        return at_cause and listed.startswith("3 ") and "\n" not in listed, f"changed: {src}; fromRecord changed: {at_cause}; list --tag: {listed!r}"
    if t.startswith("Diagnosis: bookmarks already tagged wrongly"):
        m = WRONGLY_TAGGED.search(texts)
        return bool(m), m.group(0)[:120] if m else "not named"
    if t.startswith("Diagnosis: the cause named"):
        m = re.search(r"toRecord|\bsave\(\)|`save`|save\b.{0,40}store\.ts|store\.ts.{0,80}\bsave\b", texts)
        return bool(m), m.group(0) if m else "toRecord/save not named"
    if t.startswith("Diagnosis: any source change"):
        if not src:
            return True, "no source change"
        before = git(repo, "show", f"{base}:src/store.ts")
        after = (repo / "src/store.ts").read_text() if (repo / "src/store.ts").exists() else ""
        moved = [n for n in ("listTagged", "add") if function(before, n) != function(after, n)]
        cli_changed = "src/cli.ts" in src
        listed = tags_survive_add(repo)
        ok = not moved and not cli_changed and listed.startswith("1  A")
        return ok, f"changed: {src}; symptom-side edits: {moved + (['cli.ts'] if cli_changed else [])}; list --tag after add: {listed!r}"
    if t.startswith("Diagnosis: a regression test"):
        if tests:
            failing = fails_on_base(repo, base, tests)
            return bool(failing), f"written: {tests}; fail on base: {failing}"
        first = [tasks(p)[0] for _, p in ctx["plans"] if tasks(p)]
        if first and re.search(r"\btest", first[0], re.I):
            return True, " ".join(first[0].split())[:120]
        named = [l.strip() for l in texts.splitlines()
                 if re.search(r"\btest", l, re.I) and re.search(r"\btag", l, re.I)
                 and re.search(r"\b(add|save|before|old|without|shared|other|only)", l, re.I)]
        return bool(named), named[0][:120] if named else "no test written or named"
    if t.startswith("Diagnosis: tags already lost"):
        m = LOST.search(texts)
        return bool(m), m.group(0)[:120] if m else "not named"
    if t.startswith("Contract: src/ and test/"):
        dirty = changed(repo, base, "src", "test")
        return not dirty and not committed, f"changed: {dirty}; commits: {len(committed)}"
    if t.startswith("Contract: a fix plan"):
        if not ctx["plans"]:
            return False, "no plan"
        f, p = ctx["plans"][0]
        missing = [s for s in ("Report", "Reproduction", "Root cause", "Fix", "Tasks")
                   if not re.search(rf"^#+ {s}\s*$", p, re.M | re.I)]
        return not missing, f"{f}; missing: {missing}"
    if t.startswith("Contract: the plan's first task"):
        if not ctx["plans"]:
            return False, "no plan"
        ts = tasks(ctx["plans"][0][1])
        boxes = len(re.findall(r"^\s*- \[[ x]\]", ctx["plans"][0][1], re.M))
        ok = (len(ts) >= 2 and re.search(r"\btest", ts[0], re.I) and re.search(r"end.to.end|reproduc", ts[-1], re.I)
              and boxes == len(ts))
        return bool(ok), f"{len(ts)} tasks, {boxes} boxes; first: {ts[0][:60] if ts else ''}; last: {ts[-1][:60] if ts else ''}"
    if t.startswith("Diagnosis: the report was tried"):
        quoted = [c for c in cli if re.search(r"\badd\b", c) and re.search(r"\\\"|\"[^\"]*'|'[^']*\"", c)]
        return bool(quoted), quoted[0][:120] if quoted else f"{len(cli)} CLI commands, none adds a quoted title"
    if t == "Diagnosis: no source was changed":
        return not src, f"changed: {src}"
    if t.startswith("Diagnosis: the reply says it did not reproduce"):
        m, a = NOT_REPRODUCED.search(reply), ASKS.search(reply)
        return bool(m and a), f"not reproduced: {m.group(0) if m else None}; asks: {a.group(0) if a else None}"
    if t.startswith("Contract: no fix plan"):
        return not ctx["plans"] and not committed, f"plans: {[f for f, _ in ctx['plans']]}; commits: {len(committed)}"
    raise ValueError(t)


def main(it):
    it = Path(it)
    for meta in sorted(it.glob("eval-*/eval_metadata.json")):
        spec = json.loads(meta.read_text())
        for run in sorted(meta.parent.glob("*/run-*")):
            fx = (run / "fixture").resolve()
            timing = json.loads((run / "timing.json").read_text()) if (run / "timing.json").exists() else {}
            repo, base = fx / "repo", (run / "base_sha").read_text().strip()
            ctx = {"repo": repo, "base": base, "plans": plans(repo, base),
                   "commands": commands(timing.get("session_id")),
                   "response": (run / "outputs/response.md").read_text() if (run / "outputs/response.md").exists() else ""}
            results = []
            for t in spec["assertions"]:
                ok, ev = check(t, ctx)
                results.append({"text": t, "passed": bool(ok), "evidence": ev})
            parts = {}
            for kind in ("Diagnosis", "Contract"):
                rs = [r for r in results if r["text"].startswith(kind)]
                parts[kind.lower()] = {"passed": sum(r["passed"] for r in rs), "total": len(rs)}
            n = sum(r["passed"] for r in results)
            (run / "grading.json").write_text(json.dumps({"expectations": results, "summary": {
                "passed": n, "failed": len(results) - n, "total": len(results),
                "pass_rate": round(n / len(results), 3), "parts": parts}}, indent=2))
            status = git(repo, "status", "--short")
            cli = "\n".join(c for c in ctx["commands"] if CLI.search(c))
            plan = "\n\n".join(f"== {f}\n{p}" for f, p in ctx["plans"])
            (run / "outputs/diagnosis_result.txt").write_text(f"status:\n{status}\nCLI commands:\n{cli}\n\nplans:\n{plan}\n")
            print(f"{run.relative_to(it)}: {n}/{len(results)} "
                  f"(diagnosis {parts['diagnosis']['passed']}/{parts['diagnosis']['total']}, "
                  f"contract {parts['contract']['passed']}/{parts['contract']['total']})")


if __name__ == "__main__":
    main(sys.argv[1])
