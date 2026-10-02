"""Recount executor tokens of finished runs from their session logs.

Usage: retally.py <iteration-dir>

Rewrites the token fields of each run's timing.json with session_tokens,
which includes subagents. Cost and the other fields are kept.
"""

import json
import sys
from pathlib import Path

from run_trial import session_tokens


def main():
    for meta in sorted(Path(sys.argv[1]).glob("eval-*/*/run-*/meta.json")):
        tokens = session_tokens(json.loads(meta.read_text()).get("session_id"))
        if not tokens:
            print("no session log:", meta.parent)
            continue
        timing_path = meta.parent / "timing.json"
        timing = json.loads(timing_path.read_text())
        timing.update(tokens)
        timing_path.write_text(json.dumps(timing, indent=2))


if __name__ == "__main__":
    main()
