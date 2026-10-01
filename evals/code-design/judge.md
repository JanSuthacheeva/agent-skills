You are judging implementation plans written by four different AI
planning methods for the same request in the same repository. You do not
know which method wrote which plan, and it does not matter.

The request:

{task}

The repository the plans are about is at `{repo}`. Use it to check the
plans' claims about the existing code.

The plans are in these directories, one per label. Each has the HTML
review pages and the Markdown plan the method produced:

{plans}

Judge as the repository owner who will review the plan before any code is
written and then hand it to an implementation session. The question is:
how well could you discuss and correct the code design from this plan,
before any code exists?

Score each plan from 1 to 10 on:

- correctness: claims about the codebase are true; the proposed code
  would work with the code it plugs into.
- completeness: every trigger, data change and failure path the feature
  implies is designed.
- clarity: structure, responsibilities and call flow are easy to follow;
  names say what things do.
- reviewability: you could point at a specific decision, unit or call and
  ask for it to change; open decisions are visible.

Then rank the four plans from best to worst. Do not reward length,
styling or a particular format for its own sake - a short plan that gets
the design right beats a long one that does not. Read the plans fully and
check at least three concrete claims per plan against the repository.

Reply with only this JSON:

{{"scores": {{"W": {{"correctness": 0, "completeness": 0, "clarity": 0, "reviewability": 0, "note": "one sentence"}}, "X": ..., "Y": ..., "Z": ...}}, "ranking": ["W", "X", "Y", "Z"], "reason": "two or three sentences on what separated the top plan from the rest"}}
