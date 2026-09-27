#!/usr/bin/env python3
"""Report, per run, whether the session invoked the commit skill.

Usage: skill_usage.py <iteration-dir>
Finds each run's transcript via the session_id in outputs/raw.json.
"""
import json, sys
from pathlib import Path

projects = Path.home() / ".claude" / "projects"
for raw in sorted(Path(sys.argv[1]).glob("*/*/run-*/outputs/raw.json")):
    sid = json.loads(raw.read_text()).get("session_id")
    hits = list(projects.glob(f"*/{sid}.jsonl")) if sid else []
    skills, tools = [], []
    if hits:
        for line in hits[0].read_text().splitlines():
            msg = json.loads(line).get("message", {})
            for block in msg.get("content", []) if isinstance(msg.get("content"), list) else []:
                if block.get("type") == "tool_use":
                    tools.append(block["name"])
                    if block["name"] == "Skill":
                        skills.append(block["input"].get("skill"))
    run = raw.parent.parent
    print(f"{run.parent.parent.name:30} {run.parent.name:14} {run.name}  skills={skills or '-'}  tools={len(tools)}")
