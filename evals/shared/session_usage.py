#!/usr/bin/env python3
"""Measure a headless trial from its transcripts - the main session and
every subagent it started. When agents run in the background, the harness
summary counts turns and duration of the last turn only; its cost covers
the whole session, and the estimate below is kept as a check on that.

Cost is estimated per model: the harness's reported cost is divided by
the reported tokens, weighted by fixed price ratios (output 5x input,
cache reads 0.1x, cache writes 2x), giving that run's price per weighted
token, which is applied to the transcripts' tokens.

Usage: session_usage.py <run-dir>
Reads <run>/outputs/raw.json, updates <run>/timing.json.
"""
import json, sys
from datetime import datetime
from pathlib import Path

WEIGHTS = {"input_tokens": 1, "output_tokens": 5,
           "cache_read_input_tokens": 0.1, "cache_creation_input_tokens": 2}
REPORTED = {"inputTokens": "input_tokens", "outputTokens": "output_tokens",
            "cacheReadInputTokens": "cache_read_input_tokens",
            "cacheCreationInputTokens": "cache_creation_input_tokens"}


def weighted(usage):
    return sum(usage.get(k, 0) * w for k, w in WEIGHTS.items())


def transcripts(sid):
    root = Path.home() / ".claude/projects"
    return list(root.glob(f"*/{sid}.jsonl")) + list(root.glob(f"*/{sid}/subagents/*.jsonl"))


def main(run):
    run = Path(run)
    raw = json.loads((run / "outputs/raw.json").read_text() or "{}")
    timing = json.loads((run / "timing.json").read_text())
    sid = raw.get("session_id") or timing.get("session_id")
    rate = {}
    for model, m in raw.get("modelUsage", {}).items():
        w = weighted({ours: m.get(theirs, 0) for theirs, ours in REPORTED.items()})
        if w:
            rate[model] = m.get("costUSD", 0) / w
    files = transcripts(sid) if sid else []
    messages, stamps = {}, []
    for f in files:
        for line in f.read_text().splitlines():
            e = json.loads(line)
            if e.get("timestamp"):
                stamps.append(datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00")))
            msg = e.get("message", {})
            if e.get("type") == "assistant" and "usage" in msg:
                messages[(f.name, msg.get("id"))] = (msg.get("model"), msg["usage"])
    if not messages:
        return
    fallback = max(rate.values(), default=0)
    cost = sum(weighted(u) * rate.get(model, fallback) for model, u in messages.values())
    ms = int((max(stamps) - min(stamps)).total_seconds() * 1000)
    timing.update({
        "cost_usd_reported": timing.get("cost_usd", raw.get("total_cost_usd", 0)),
        "cost_usd": round(cost, 4),
        "output_tokens": sum(u.get("output_tokens", 0) for _, u in messages.values()),
        "num_turns": len(messages),
        "duration_ms": ms, "total_duration_seconds": round(ms / 1000, 1),
        "subagents": len(files) - 1})
    (run / "timing.json").write_text(json.dumps(timing))


if __name__ == "__main__":
    for r in sys.argv[1:]:
        main(r)
