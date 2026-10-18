#!/usr/bin/env python3
"""Grade one setup-saaio eval run by using what it wrote, the way saaio would.

Usage: grade.py <run-dir> <eval-name>
Checks the files, then plays saaio: a fresh worktree on slot 7 with the run's
uncommitted changes applied (as a commit would bring them), .saaio/setup,
a request to the service, .saaio/teardown. Writes <run>/grading.json and
cleans up every worktree, branch and container the run or the grader left.
"""
import json, os, re, signal, subprocess, sys, time, urllib.request
from pathlib import Path

run = Path(sys.argv[1]); name = sys.argv[2]
repo = (run / "repo").resolve()
response = (run / "outputs/response.md").read_text() if (run / "outputs/response.md").exists() else ""
base = (run / "base_sha").read_text().strip()
meta = json.loads((run.parent.parent / "eval_metadata.json").read_text())
notes = []


def sh(*args, cwd=None, env=None, timeout=60):
    try:
        p = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()
    except subprocess.TimeoutExpired:
        return 124, "timed out"


def git(*args):
    return sh("git", "-C", str(repo), *args)[1]


def containers(under: Path):
    out = sh("docker", "ps", "-a", "--format", '{{.ID}} {{.Label "com.docker.compose.project.working_dir"}}')[1]
    return [line.split()[0] for line in out.splitlines()
            if len(line.split()) > 1 and line.split()[1].startswith(str(under))]


def get(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return r.status
    except Exception as error:
        return str(error)


def executable(path: Path):
    return path.is_file() and os.access(path, os.X_OK)


setup, teardown = repo / ".saaio/setup", repo / ".saaio/teardown"
compose = next((repo / f for f in ("compose.yaml", "compose.yml", "docker-compose.yml") if (repo / f).exists()), None)
compose_text = compose.read_text() if compose else ""

compose_committed = bool(compose) and bool(git("diff", "--stat", base, "HEAD", "--", compose.name).strip()) \
    and not git("status", "--porcelain", "--", compose.name).strip()

# What the run left behind, before the grader adds its own worktree.
worktrees = [l for l in git("worktree", "list", "--porcelain").splitlines() if l.startswith("worktree ")]
branches = [b.strip("* ").strip() for b in git("branch", "--format=%(refname:short)").splitlines()]
leftover = containers(repo)
clean_after_run = len(worktrees) == 1 and branches == ["main"] and not leftover
left_evidence = f"worktrees={len(worktrees)} branches={branches} containers={len(leftover)}"

# Play saaio on slot 7.
wt = repo / ".saaio/worktrees/grade-check"
env = dict(os.environ, SAAIO_SLOT="7", SAAIO_WORKTREE=str(wt), SAAIO_REPO=str(repo),
           SAAIO_FLOW_NAME="grade-check", SAAIO_FLOW_ID="grade-check")
served = served_evidence = None
setup_ok = teardown_ok = False
teardown_evidence = "not run"
if executable(setup):
    git("worktree", "add", "-q", str(wt), "-b", "grade-check")
    diff = subprocess.run(["git", "-C", str(repo), "diff", base], capture_output=True, text=True).stdout
    if diff:
        subprocess.run(["git", "-C", str(wt), "apply"], input=diff, text=True, capture_output=True)
    code, out = sh(str(setup), cwd=wt, env=env, timeout=600)
    setup_ok = code == 0
    notes.append(f"setup exit {code}: {out[-400:]}")
    if name == "dev-server":
        proc = subprocess.Popen(["npm", "run", "dev"], cwd=wt, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, start_new_session=True)
        assert proc.stdout is not None
        port, deadline = None, time.time() + 15
        while time.time() < deadline and port is None:
            line = proc.stdout.readline()
            m = re.search(r"localhost:(\d+)", line or "")
            port = int(m.group(1)) if m else None
        status = get(f"http://localhost:{port}/") if port else "no port printed"
        served = port not in (None, 5173) and status == 200
        served_evidence = f"npm run dev on {port}: {status}"
        os.killpg(proc.pid, signal.SIGTERM)
    elif setup_ok:
        service = "web" if name == "compose-hardcoded-ports" else "laravel.test"
        out = sh("docker", "compose", "port", service, "80", cwd=wt, env=env)[1]
        m = re.search(r":(\d+)\s*$", out)
        port = int(m.group(1)) if m else None
        status = get(f"http://localhost:{port}/") if port else out
        served = port not in (None, 8080, 80) and status == 200
        served_evidence = f"{service} on {port}: {status}"
    if executable(teardown):
        code, out = sh(str(teardown), cwd=wt, env=env, timeout=300)
        gone = not containers(wt)
        teardown_ok = code == 0 and gone
        teardown_evidence = f"exit {code}, containers left: {len(containers(wt))}; {out[-200:]}"

# Clean up whatever is left.
for cid in containers(repo):
    sh("docker", "rm", "-f", "-v", cid)
for line in git("worktree", "list", "--porcelain").splitlines()[1:]:
    if line.startswith("worktree "):
        git("worktree", "remove", "--force", line[len("worktree "):])
for branch in git("branch", "--format=%(refname:short)").splitlines():
    if branch != "main":
        git("branch", "-D", branch)
sh("docker", "volume", "prune", "-f", "--filter", "label=com.docker.compose.project=grade-check")

said_dry_run = bool(re.search(
    r"dry run|scratch worktree|setup-saaio-check|slot (9|20)\b|\btested\b|\bto test it\b|\*\*test:?\*\*"
    r"|simulated workers?|temporary (copies|worktrees?)", response, re.I))
compose_changed = git("diff", base, "--stat", "--", "docker-compose.yml").strip()


def verdict(text):
    if text.startswith("compose.yaml publishes both ports"):
        ok = bool(re.search(r'\$\{\w+:-8080\}:80', compose_text)) and bool(re.search(r'\$\{\w+:-6379\}:6379', compose_text))
        return ok, re.findall(r'"?\S*:\d+"?$', compose_text, re.M)
    if text.startswith("compose.yaml has no container_name"):
        return "container_name" not in compose_text, "container_name present" if "container_name" in compose_text else "none"
    if text.startswith(".saaio/setup exists and is executable"):
        return executable(setup), f"setup={executable(setup)}"
    if text.startswith("If .saaio/teardown exists"):
        return (not teardown.exists()) or teardown_ok, teardown_evidence if teardown.exists() else "no teardown"
    if text.startswith(".saaio/setup and .saaio/teardown exist"):
        return executable(setup) and executable(teardown), f"setup={executable(setup)} teardown={executable(teardown)}"
    if text.startswith("In a fresh worktree") or text.startswith("In a fresh worktree on slot 7, npm"):
        return bool(served), served_evidence or "; ".join(notes)[-300:]
    if text.startswith(".saaio/teardown removes") or text.startswith(".saaio/teardown runs"):
        return teardown_ok, teardown_evidence
    if text.startswith("The dry run left no"):
        return clean_after_run, left_evidence
    if text.startswith("The response reports what the dry run"):
        return said_dry_run, response[-300:]
    if text.startswith("No compose file"):
        return compose is None, str(compose)
    if text.startswith("docker-compose.yml is unchanged"):
        return not compose_changed, compose_changed or "unchanged"
    if text.startswith(".saaio/setup sets APP_PORT and FORWARD_REDIS_PORT"):
        body = setup.read_text() if setup.exists() else ""
        ok = "APP_PORT" in body and "FORWARD_REDIS_PORT" in body and "SAAIO_SLOT" in body
        return ok, "both named with SAAIO_SLOT" if ok else "missing"
    if text.startswith("The compose change is committed, or the response says"):
        if compose_committed:
            return True, "compose change committed"
        said = re.search(r"[^.\n]*\bcommit[^.\n]*\b(reach|worktree|worker|flow)[^.\n]*"
                         r"|[^.\n]*\b(reach|worktree|worker|flow)[^.\n]*\bcommit[^.\n]*", response, re.I)
        return bool(said), said.group(0).strip() if said else response[-200:]
    return False, "no check for this expectation"


results = []
for text in meta["assertions"]:
    passed, evidence = verdict(text)
    results.append({"text": text, "passed": bool(passed), "evidence": str(evidence)[:500]})
passed = sum(r["passed"] for r in results)
(run / "grading.json").write_text(json.dumps({
    "expectations": results,
    "summary": {"passed": passed, "failed": len(results) - passed, "total": len(results),
                "pass_rate": round(passed / len(results), 2) if results else 0},
    "notes": notes}, indent=2))
print(f"{run}: {passed}/{len(results)}")
