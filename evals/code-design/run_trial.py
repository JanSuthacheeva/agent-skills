"""Run one code-design eval trial: the executor plans, a simulated user answers.

Usage: run_trial.py <eval-id> <config> <run-dir>

The executor runs headless in a fresh fixture clone with the config's
invocation and settings. Whenever it ends a turn, the simulated user reads
its last message and the plan pages it changed, then replies. The loop ends
one turn after the user approves, or at MAX_TURNS.
"""

import json
import os
import shutil
import subprocess
import sys
import time
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXECUTOR_MODEL = os.environ.get("MODEL", "claude-opus-5-5")
USER_MODEL = os.environ.get("USER_MODEL", "claude-sonnet-5-5")
MAX_TURNS = int(os.environ.get("MAX_TURNS", "14"))
TURN_TIMEOUT = 45 * 60
ARTIFACT_CHARS = 60_000
PLAN_SUFFIXES = {".html", ".md"}
MAX_COLLECT_BYTES = 1_000_000
ALLOWED_TOOLS = ["Bash", "Read", "Glob", "Grep", "Write", "Edit", "Agent", "Skill", "WebFetch", "WebSearch", "ToolSearch"]
DENIED_COMMANDS = ["Bash(git push:*)", "Bash(git remote:*)"]
OUTPUT_RULES = (
    "Deliver the final plan as a lavish HTML page under .lavish/ and as a "
    "Markdown file at .lavish/<slug>.md (this location overrides any other "
    "plan location; when to write it is up to your method). Do not open a "
    "browser and do not run lavish-axi open, poll or end. When you need a "
    "decision or input from the user, ask in your reply and end your turn. "
    "Do not implement any code."
)


APPROVAL_NOTE = (
    "(Planning is finished. Make sure the final plan files are written, "
    "then stop. Do not implement anything.)"
)


class TextExtractor(HTMLParser):
    BLOCKS = {"p", "div", "li", "tr", "h1", "h2", "h3", "h4", "section", "br", "pre", "label", "td", "th"}

    def __init__(self):
        super().__init__()
        self.parts, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        elif tag == "input":
            a = dict(attrs)
            self.parts.append(f" [{a.get('type', 'text')} {a.get('name', '')}={a.get('value', '')}] ")
        elif tag in self.BLOCKS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def page_text(path: Path) -> str:
    raw = path.read_text(errors="ignore")
    if path.suffix == ".html":
        parser = TextExtractor()
        parser.feed(raw)
        raw = "".join(parser.parts)
    lines = [line.strip() for line in raw.splitlines()]
    return "\n".join(line for line in lines if line)[:ARTIFACT_CHARS]


def claude(args: list[str], cwd: Path) -> dict:
    proc = subprocess.run(["claude", *args], cwd=cwd, stdin=subprocess.DEVNULL,
                          capture_output=True, text=True, timeout=TURN_TIMEOUT)
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"is_error": True, "result": "", "stderr": proc.stderr[-4000:], "stdout": proc.stdout[-4000:]}


def changed_files(repo: Path, base: str) -> dict[str, float]:
    git = lambda *args: subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True).stdout
    status = [line[3:].strip('"') for line in git("status", "--porcelain", "-uall", "--ignored").splitlines()]
    committed = git("diff", "--name-only", base).splitlines()
    files = {}
    for rel in status + committed:
        path = repo / rel
        if path.is_file() and ".git/" not in rel and path.stat().st_size <= MAX_COLLECT_BYTES:
            files[rel] = path.stat().st_mtime
    return files


def executor_settings(cfg: dict) -> str:
    return json.dumps({
        "enabledPlugins": {plugin: False for plugin in cfg["plugins_off"]},
        "permissions": {"deny": cfg["deny"] + DENIED_COMMANDS},
    })


def run_executor(message: str, session: str | None, cfg: dict, repo: Path) -> dict:
    args = ["-p", message, "--output-format", "json", "--model", EXECUTOR_MODEL,
            "--permission-mode", "acceptEdits", "--settings", executor_settings(cfg),
            "--allowedTools", *ALLOWED_TOOLS,
            "--append-system-prompt", OUTPUT_RULES, "--disallowedTools", "AskUserQuestion"]
    if session:
        args += ["--resume", session]
    return claude(args, repo)


def run_user(scenario: dict, conversation: list[tuple[str, str]], artifacts: dict[str, str], cwd: Path) -> dict:
    template = (HERE / "sim_user.md").read_text()
    prompt = template.format(
        task=scenario["prompt"],
        preferences="\n".join(f"- {p}" for p in scenario["preferences"]),
        conversation="\n\n".join(f"{role.upper()}:\n{text}" for role, text in conversation),
        artifacts="\n\n".join(f"=== {name} ===\n{text}" for name, text in artifacts.items()) or "(none)",
    )
    return claude(["-p", prompt, "--output-format", "json", "--model", USER_MODEL,
                   "--tools", "", "--setting-sources", ""], cwd)


def usage(result: dict) -> dict:
    """Per-invocation usage. cost_usd is cumulative for the session on --resume."""
    u = result.get("usage", {})
    return {
        "tokens": sum(u.get(k, 0) for k in ("input_tokens", "output_tokens", "cache_creation_input_tokens")),
        "output_tokens": u.get("output_tokens", 0),
        "cache_read_tokens": u.get("cache_read_input_tokens", 0),
        "cost_usd": result.get("total_cost_usd", 0),
        "duration_ms": result.get("duration_ms", 0),
        "num_turns": result.get("num_turns", 0),
    }


def skills_invoked(session: str | None) -> list[str] | None:
    hits = list((Path.home() / ".claude" / "projects").glob(f"*/{session}.jsonl")) if session else []
    if not hits:
        return None
    calls, blocked = {}, set()
    for line in hits[0].read_text().splitlines():
        content = json.loads(line).get("message", {}).get("content")
        for block in content if isinstance(content, list) else []:
            if block.get("type") == "tool_use" and block.get("name") == "Skill":
                calls[block["id"]] = block["input"].get("skill")
            elif block.get("type") == "tool_result" and block.get("is_error"):
                blocked.add(block.get("tool_use_id"))
    return [skill for call, skill in calls.items() if call not in blocked]


def clone_fixture(fixture: dict, repo: Path):
    source = os.path.expanduser(fixture["source"])
    subprocess.run(["git", "clone", "-q", source, str(repo)], check=True)
    subprocess.run(["git", "checkout", "-q", fixture["sha"]], cwd=repo, check=True)
    subprocess.run(["git", "remote", "remove", "origin"], cwd=repo, check=True)


def collect_outputs(repo: Path, base: str, outputs: Path):
    for rel in changed_files(repo, base):
        src = repo / rel
        dest = outputs / "files" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        if src.suffix in PLAN_SUFFIXES:
            flat = outputs / rel.replace("/", "__").lstrip(".")
            shutil.copy2(src, flat)


def main():
    eval_id, config_name, run_dir = int(sys.argv[1]), sys.argv[2], Path(sys.argv[3]).resolve()
    scenario = next(e for e in json.loads((HERE / "evals.json").read_text())["evals"] if e["id"] == eval_id)
    cfg = json.loads((HERE / "configs.json").read_text())[config_name]
    repo, outputs = run_dir / "repo", run_dir / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)
    clone_fixture(scenario["fixture"], repo)

    started = time.time()
    message = cfg["invoke"].format(task=scenario["prompt"])
    session, conversation, transcript = None, [], []
    executor_turns, user_turns = [], []
    approved, errored = False, False
    base = scenario["fixture"]["sha"]
    seen = changed_files(repo, base)

    while True:
        result = run_executor(message, session, cfg, repo)
        session = result.get("session_id", session)
        executor_turns.append(usage(result))
        reply = result.get("result", "") or f"(executor error: {result.get('stderr', '')})"
        conversation.append(("assistant", reply))
        transcript.append(f"## Executor turn {len(executor_turns)}\n\n{reply}")
        errored = bool(result.get("is_error"))
        if approved or errored or len(executor_turns) >= MAX_TURNS:
            break

        now = changed_files(repo, base)
        artifacts = {rel: page_text(repo / rel) for rel, mtime in now.items()
                     if Path(rel).suffix in PLAN_SUFFIXES and seen.get(rel) != mtime}
        seen = now

        answer = run_user(scenario, conversation, artifacts, run_dir)
        user_turns.append(usage(answer))
        message = answer.get("result", "").strip() or "Please continue."
        conversation.append(("user", message))
        transcript.append(f"## Simulated user turn {len(user_turns)}\n\n{message}")
        approved = message.startswith("APPROVED")
        if approved:
            message += "\n\n" + APPROVAL_NOTE

    collect_outputs(repo, base, outputs)
    touched_code = sorted(rel for rel in changed_files(repo, base)
                          if Path(rel).suffix not in PLAN_SUFFIXES and not rel.startswith(".lavish/"))
    invocation = cfg["invoke"].format(task=scenario["prompt"])
    (outputs / "transcript.md").write_text(f"## Eval Prompt\n\n{invocation}\n\n" + "\n\n".join(transcript) + "\n")

    total = lambda turns, key: sum(t[key] for t in turns)
    timing = {
        "total_tokens": total(executor_turns, "tokens"),
        "output_tokens": total(executor_turns, "output_tokens"),
        "cache_read_tokens": total(executor_turns, "cache_read_tokens"),
        "cost_usd": round(executor_turns[-1]["cost_usd"], 4),
        "executor_duration_ms": total(executor_turns, "duration_ms"),
        "total_duration_seconds": round(time.time() - started, 1),
        "executor_turns": len(executor_turns),
        "executor_tool_turns": total(executor_turns, "num_turns"),
        "user_tokens": total(user_turns, "tokens"),
        "user_cost_usd": round(total(user_turns, "cost_usd"), 4),
    }
    (run_dir / "timing.json").write_text(json.dumps(timing, indent=2))
    (run_dir / "meta.json").write_text(json.dumps({
        "config": config_name, "eval_id": eval_id, "session_id": session,
        "approved": approved, "errored": errored,
        "capped": not approved and not errored, "touched_code": touched_code, "skills": skills_invoked(session),
    }, indent=2))


if __name__ == "__main__":
    main()
