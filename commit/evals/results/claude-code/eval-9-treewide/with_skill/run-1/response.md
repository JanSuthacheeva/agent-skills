I committed the staged changes as one commit (578fd3c) on `main`:

```
treewide: add MIT license
```

It adds the `LICENSE` file and a License section to `README.md`, and puts an MIT license header comment at the top of all five Python files. I used the `treewide` scope because the change spans `api`, `billing` and `worker`. The branch name has no ticket ID, so there's no `Refs:` line.