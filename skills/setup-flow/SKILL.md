---
name: setup-flow
description: >-
  Prepares a repository so flow (github.com/JanSuthacheeva/flow) can run
  several workers side by side, each in its own git worktree with its own
  ports, containers and env: reads how the project runs (Docker Compose,
  Laravel Sail, npm/pnpm/vite or artisan dev servers, .env files), makes
  compose ports configurable, writes .flow/setup and .flow/teardown that
  take their ports from FLOW_SLOT, and proves them in a scratch worktree.
  Use when the user asks to set up flow for a project, make a repo ready
  for parallel worktrees or agents, write the flow setup/teardown hooks,
  or fix port or container clashes between worktrees, even if they just
  say "get this repo ready for flow". Not for installing flow itself or
  for starting a flow.
compatibility: >-
  Requires git. Docker with Compose for container projects; the dry run
  needs it running.
metadata:
    author: Jan Suthacheeva
    version: "0.1"
---

flow runs each worker in `.flow/worktrees/<name>` on its own branch. When
the project needs services (a database, a web server, a dev server), two
workers on the same ports or container names break each other, and a
fresh worktree has no `.env` and no installed dependencies. This skill
gives each worktree its own stack, numbered by its slot, so workers never
collide and the checkout you work in stays as it is.

## What flow gives the hooks

`flow start` runs `<repo>/.flow/setup` after creating the worktree and
before the worker starts; `flow clear` and `flow remove` run
`.flow/teardown` before removing it. Both run with the worktree as their
working directory and get:

| Variable | Value |
| --- | --- |
| `FLOW_SLOT` | 1 to 20, unique among unfinished flows in every project |
| `FLOW_WORKTREE` | the worktree's absolute path |
| `FLOW_REPO` | the main checkout's absolute path |
| `FLOW_NAME` | the flow's name, e.g. `shop-217` |
| `FLOW_ID` | the flow's id |

The worker's session gets the same variables. `flow start` waits for
setup, so keep it as quick as the project allows. A setup that exits
non-zero marks the flow blocked with its last output line, so make the
last line of every failure say what went wrong.

flow runs the hooks from the main checkout, so they work uncommitted, but
it creates every worktree from the last commit: a compose or `.gitignore`
change reaches workers only once it is committed.

## Workflow

1. **Read how the project runs.** In one pass: `compose.yaml`,
   `compose.yml`, `docker-compose.yml` (and overrides), `composer.json`
   (`laravel/sail`), `package.json` scripts, `vite.config.*`, `Makefile`,
   `.env.example` and `.env` (names only, never print secret values), the
   README's setup section, `CLAUDE.md`/`AGENTS.md`, an existing `.flow/`
   folder and `.gitignore`. Note every port the host sees (published
   compose ports, Sail's `APP_PORT`/`FORWARD_*_PORT`/`VITE_PORT`, dev
   server ports), every fixed `container_name`, fixed volume or network
   names, how dependencies get installed and how the database gets its
   schema and seed data. If the repo already has `.flow/setup`, improve it
   rather than starting over.

2. **Plan a port per service and slot.** A worktree's port is the
   service's usual port plus 10000 plus the slot: MySQL 3306 becomes
   13306 + slot, a web server on 8080 becomes 18080 + slot. Check that the
   twenty ports of each service (`base + 1` to `base + 20`) overlap no
   other service's and stay below 65536; where they would, move that
   service to a free range and say so. Name each port by the variable the
   project already uses (Sail's `APP_PORT`, `FORWARD_DB_PORT`, an existing
   `${HTTP_PORT}` in compose); otherwise `<SERVICE>_PORT`. Show the plan
   as a table: service, variable, usual port, worktree port for slot 1.

3. **Make compose configurable, keeping today's ports.** Rewrite each
   published port to read its variable with the current port as default,
   `"8080:80"` becoming `"${HTTP_PORT:-8080}:80"`, so `docker compose up`
   without flow does exactly what it did. Remove fixed `container_name`
   entries (compose names containers after the project) and flag fixed
   volume or network names that would be shared. Show the diff and write
   it only after the user approves: it changes a file the whole team
   uses. Sail's compose file already reads `.env`, so it usually needs no
   change.

4. **Write `.flow/setup`.** A bash script, `set -euo pipefail`, that:
   - computes each port from `FLOW_SLOT`;
   - writes the worktree's `.env` from `$FLOW_REPO/.env` (else
     `.env.example`), replacing or appending the port variables,
     `COMPOSE_PROJECT_NAME="$(basename "$FLOW_REPO")-$FLOW_NAME"` (compose
     reads it from `.env`, so the worker's own `docker compose` commands
     reach the same stack) and URLs that carry a port (`APP_URL`). Two
     repos can have flows of the same name, which is why the project name
     carries the repo; lowercase it and turn anything but letters, digits,
     `-` and `_` into `-`, as compose accepts nothing else;
   - installs dependencies the way the README does (`composer install`,
     `npm ci`), inside a container when the project has no local tooling;
   - starts the stack (`docker compose up -d --wait`, or `sail up -d`),
     then migrates and seeds inside it;
   - starts no foreground dev server (setup has to return): the worker
     runs `npm run dev` itself, on the `VITE_PORT`/`PORT` in its `.env`;
   - ends by printing where the services answer, one line each.

5. **Write `.flow/teardown`** when there is something to clean up (a
   project with only dev servers has none: removing the worktree removes
   its `.env`). From the worktree, stop and remove the
   stack with its volumes (`docker compose down -v --remove-orphans`, or
   `sail down -v`). It must not fail on a worktree whose setup failed
   halfway: guard each step so a missing `.env` or stack is not an error.

6. **Make them work in git.** `chmod +x` both scripts. Make sure
   `.gitignore` ignores `.flow/worktrees/`, so the main checkout does not
   see the worktrees as untracked files.

7. **Prove it in a scratch worktree.** Use slot 20 (the one real flows
   reach last; with flow installed, check `flow status --all` and pick a
   free one): `git worktree add .flow/worktrees/setup-flow-check -b
   setup-flow-check`, bring the uncommitted changes into it
   (`git diff HEAD | git -C <worktree> apply`), as a commit would, run
   `.flow/setup` there with the five variables
   set, check that each service answers on its slot port (`curl` for
   HTTP, `nc -z` or a client for the rest) and that a stack already
   running in the main checkout is untouched. Then run `.flow/teardown`,
   check its containers and volumes are gone, and remove the worktree and
   branch (`git worktree remove --force`, `git branch -D`). Fix what
   fails and run it again. Without Docker running, say so and give the
   command to run the check later.

8. **Offer the branch convention.** If the project's rules
   (`CLAUDE.md`, `CONTRIBUTING.md`, the README) name a branch convention,
   offer `.flow/config.toml`:
   ```toml
   [branch]
   name  = "{type}/{ticket}-{slug}"
   types = ["feature", "bugfix", "hotfix", "chore"]
   ```
   `{ticket}` is the request's ticket key, `{slug}` up to five words after
   it, `{name}` the flow's name; the first type is the default.

9. **Hand over.** List the files changed and the port table, and say
   what the dry run showed. Say that the compose and `.gitignore` changes
   take effect for flows once committed, and offer to commit them with the
   scripts (so the team gets them too). Commit when the user asks for a
   commit, now or as a standing rule in their instructions ("commit as you
   go"); otherwise leave the changes and say what to commit. A commit goes
   into the history the whole team shares, and the user may want to read
   the compose diff first, so permission to change files is not permission
   to commit.

## Example

A Laravel project whose `compose.yaml` publishes `"8080:80"` (nginx) and
`"3306:3306"` (mysql), with a fixed `container_name: shop-db`:

- compose: `"${HTTP_PORT:-8080}:80"`, `"${DB_PORT:-3306}:3306"`,
  `container_name` removed;
- `.flow/setup`: `HTTP_PORT=$((18080 + FLOW_SLOT))`,
  `DB_PORT=$((13306 + FLOW_SLOT))`, `.env` with those, `APP_URL` on the
  HTTP port and `COMPOSE_PROJECT_NAME=shop-<flow name>`;
  `docker compose up -d --wait`;
  `docker compose exec -T php php artisan migrate --seed --force`; prints
  `http://localhost:18083` and `mysql 127.0.0.1:13309` for slot 3;
- `.flow/teardown`: `docker compose down -v --remove-orphans`.
