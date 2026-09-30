"""Check that file:line citations in a run's outputs exist in its repo clone.

Usage: python check_citations.py <run_dir>
Prints JSON: {"total": n, "valid": n, "invalid": [...]}.
"""

import json
import re
import sys
from pathlib import Path

CITATION = re.compile(r"([\w./-]+\.[a-z]{1,5}):(\d+)(?:[-–](\d+))?")


def citations(outputs: Path):
    for path in outputs.rglob("*"):
        if path.suffix in {".html", ".md"}:
            yield from CITATION.findall(path.read_text(errors="ignore"))


def resolve(repo: Path, name: str):
    direct = repo / name
    if direct.is_file():
        return [direct]
    matches = [p for p in repo.rglob(Path(name).name) if ".git" not in p.parts]
    return [p for p in matches if str(p).endswith(name)]


def main():
    run = Path(sys.argv[1])
    repo, outputs = run / "repo", run / "outputs"
    seen, invalid, ambiguous = set(), [], []
    for name, start, end in citations(outputs):
        key = (name, start, end)
        if key in seen or name.startswith(("http", "//")):
            continue
        seen.add(key)
        files = resolve(repo, name)
        last = int(end or start)
        if not files:
            invalid.append(f"{name}:{start} (file not found)")
        elif all(last > len(f.read_text(errors="ignore").splitlines()) for f in files):
            invalid.append(f"{name}:{start} (past end of file)")
        elif len(files) > 1:
            ambiguous.append(f"{name}:{start}")
    print(json.dumps({"total": len(seen), "valid": len(seen) - len(invalid), "invalid": invalid, "ambiguous": ambiguous}, indent=2))


if __name__ == "__main__":
    main()
