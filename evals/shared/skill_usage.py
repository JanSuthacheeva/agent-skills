#!/usr/bin/env python3
"""Report, per run, which skills the session invoked.

Usage: skill_usage.py <iteration-dir>
Finds each run's transcript via the session_id in outputs/raw.json.
"""
import json, sys
from pathlib import Path

PROJECTS = Path.home() / ".claude" / "projects"


def skills_invoked(raw_path):
    """Skill names the run's session invoked, or None if its transcript is gone."""
    sid = json.loads(Path(raw_path).read_text()).get("session_id")
    hits = list(PROJECTS.glob(f"*/{sid}.jsonl")) if sid else []
    if not hits:
        return None
    skills = []
    for line in hits[0].read_text().splitlines():
        content = json.loads(line).get("message", {}).get("content")
        for block in content if isinstance(content, list) else []:
            if block.get("type") == "tool_use" and block["name"] == "Skill":
                skills.append(block["input"].get("skill"))
    return skills


if __name__ == "__main__":
    for raw in sorted(Path(sys.argv[1]).glob("*/*/run-*/outputs/raw.json")):
        run = raw.parent.parent
        skills = skills_invoked(raw)
        shown = "transcript missing" if skills is None else (skills or "-")
        print(f"{run.parent.parent.name:30} {run.parent.name:14} {run.name}  skills={shown}")
