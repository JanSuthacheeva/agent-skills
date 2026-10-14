You are judging the reports that {count} different code review methods
left for the owner of a branch after reviewing it and fixing what they
found. You do not know which method wrote which report, and it does not
matter.

The request each method got:

{task}

The branch implements a planned feature. These problems were planted in
it on purpose, so you know where the real risk was:

{planted}

Each label below has the method's report (`report.md`) and a copy of the
repository as the method left it (`repo/`, with its git history):

{labels}

Judge as the owner, a busy engineer who wants to stay confident in the
code without reading every line. The question is: after reading this
report, do you know what was wrong, what changed, what still needs your
decision, and where to look?

Score each report from 1 to 10 on:

- accuracy: what the report says was wrong, fixed or left open is true.
  Check at least three claims per report against its `repo/` (code, git
  log, running the tests or the CLI).
- risk: it points you at the places that carry the real risk - above all
  the planted problems - in an order you could follow, and says what is
  routine; it does not bury them among minor points.
- decisions: choices that users would notice or that are expensive to
  undo are put to you with a recommendation, not made silently or hidden.
- readability: you grasp the state of the branch in about two minutes.

Then rank the reports from best to worst. Do not reward length or a
particular format for its own sake; judge what the owner gets out of it.

Reply with only this JSON:

{{"scores": {{"X": {{"accuracy": 0, "risk": 0, "decisions": 0, "readability": 0, "note": "one sentence"}}, "Y": ..., "Z": ...}}, "ranking": ["X", "Y", "Z"], "reason": "two or three sentences on what separated the best report from the rest"}}
