## Successful trials (all checks passed)

| Scenario | v0.7 | v0.8 | v0.8 invoked /security-review |
|---|---|---|---|
| seeded-defects | 3/3 | 3/3 | 3/3 |
| vague-prompt | 3/3 | 3/3 | 3/3 |
| architecture | 3/3 | 3/3 | 3/3 |
| security-diff | 3/3 | 3/3 | 3/3 |
| stacked-base | 3/3 | 0/3 | 3/3 |
| no-origin-head | 3/3 | 3/3 | 0/3 |
| clean-branch | 3/3 | 3/3 | 3/3 |
| subtle-xss | 3/3 | 3/3 | 3/3 |


## Failed checks (number of trials)

| Version | Scenario | Check | Trials |
|---|---|---|---|
| v0.8 | stacked-base | Response does not report the lower branch's injection | 3 |


## Blind judge, owner report total of 40, mean (sd)

| Scenario | v0.7 | v0.8 |
|---|---|---|
| seeded-defects | 33.0 (2.6) | 34.7 (0.6) |
| vague-prompt | 35.0 (1.0) | 31.7 (2.3) |
| architecture | 34.0 (0.0) | 35.7 (0.6) |
| security-diff | 35.0 (0.0) | 32.3 (4.7) |
| stacked-base | 31.7 (2.9) | 34.7 (0.6) |
| no-origin-head | 34.7 (0.6) | 33.3 (1.2) |
| clean-branch | 33.7 (1.5) | 32.3 (3.2) |
| subtle-xss | 35.3 (1.2) | 34.3 (0.6) |
| All | 34.0 (1.8) | 33.6 (2.3) |
| Ranked first | 14/24 | 10/24 |


## Resource use per trial, mean (sd)

| Measure | v0.7 | v0.8 |
|---|---|---|
| Cost (USD) | 0.48 (0.11) | 0.79 (0.23) |
| Duration (s) | 112 (24) | 167 (241) |
| Output tokens | 10533 (2439) | 15631 (6267) |
| Subagents | 1.0 (0.0) | 2.8 (1.1) |
