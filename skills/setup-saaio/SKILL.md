---
name: setup-saaio
description: >-
  Prepares a repository so saaio (github.com/JanSuthacheeva/saaio) can run
  several workers side by side, each in its own git worktree with its own
  ports, containers and env: reads how the project runs (Docker Compose,
  Laravel Sail, npm/pnpm/vite or artisan dev servers, .env files), makes
  compose ports configurable, writes .saaio/setup and .saaio/teardown that
  take their ports from SAAIO_SLOT, and .saaio/pause and .saaio/resume that
  stop and start a resting flow's stack, and proves them in a scratch
  worktree.
  Use when the user asks to set up saaio for a project, make a repo ready
  for parallel worktrees or agents, write the saaio setup/teardown hooks,
  write the pause/resume hooks, or fix port or container clashes between
  worktrees, even if they just
  say "get this repo ready for saaio". Not for installing saaio itself or
  for starting a flow.
compatibility: >-
  Requires git. Docker with Compose for container projects; the dry run
  needs it running.
metadata:
    author: Jan Suthacheeva
    version: "0.3"
---

saaio runs each worker in `.saaio/worktrees/<name>` on its own branch. When
the project needs services (a database, a web server, a dev server), two
workers on the same ports or container names break each other, and a
fresh worktree has no `.env` and no installed dependencies. This skill
gives each worktree its own stack, numbered by its slot, so workers never
collide and the checkout you work in stays as it is, and stops a stack
while its flow rests, so many flows do not hold CPU and memory for nothing.

## What saaio gives the hooks

`saaio start` runs `<repo>/.saaio/setup` after creating the worktree and
before the worker starts; `saaio clear` and `saaio remove` run
`.saaio/teardown` before removing it. Both run with the worktree as their
working directory and get:

| Variable | Value |
| --- | --- |
| `SAAIO_SLOT` | 1 to 20, unique among unfinished flows in every project |
| `SAAIO_WORKTREE` | the worktree's absolute path |
| `SAAIO_REPO` | the main checkout's absolute path |
| `SAAIO_FLOW_NAME` | the flow's name, e.g. `shop-217` |
| `SAAIO_FLOW_ID` | the flow's id |

`saaio server` runs `.saaio/pause` when a flow has rested (idle, waiting,
blocked, done or ended) for a few minutes, and `.saaio/resume` when its
worker works again; the worker's tool calls wait for the resume, up to two
minutes. They run the same way, with the same variables, at most five
minutes each. saaio pauses only a repo that has both. A server that stops
mid-script runs it again, and the scripts can meet a stack in any state, so
both must be idempotent.

The worker's session gets the same variables. `saaio start` waits for
setup, so keep it as quick as the project allows. A setup that exits
non-zero marks the flow blocked with its last line on stderr (stdout
only when stderr is empty), so end every failure with a message on
stderr (`echo "failed: ..." >&2`) that says what went wrong: tools such
as `docker compose` write their progress there too.

saaio runs the hooks from the main checkout, so they work uncommitted, but
it creates every worktree from the last commit: a compose change reaches
workers only once it is committed. saaio keeps `.saaio/worktrees/` out of
git itself, in `.git/info/exclude`.

## Workflow

1. **Read how the project runs.** In one pass: `compose.yaml`,
   `compose.yml`, `docker-compose.yml` (and overrides), `composer.json`
   (`laravel/sail`), `package.json` scripts, `vite.config.*`, `Makefile`,
   `.env.example` and `.env` (names only, never print secret values), the
   README's setup section, `CLAUDE.md`/`AGENTS.md` and an existing
   `.saaio/` folder. Note every port the host sees (published
   compose ports, Sail's `APP_PORT`/`FORWARD_*_PORT`/`VITE_PORT`, dev
   server ports), every fixed `container_name`, fixed volume or network
   names, how dependencies get installed and how the database gets its
   schema and seed data. If the repo already has `.saaio/setup`, improve it
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
   without saaio does exactly what it did. Remove fixed `container_name`
   entries (compose names containers after the project) and flag fixed
   volume or network names that would be shared. Show the diff and write
   it only after the user approves: it changes a file the whole team
   uses. Sail's compose file already reads `.env`, so it usually needs no
   change.

4. **Write `.saaio/setup`.** A bash script, `set -euo pipefail`, that:
   - computes each port from `SAAIO_SLOT`;
   - writes the worktree's `.env` from `$SAAIO_REPO/.env` (else
     `.env.example`), replacing or appending the port variables,
     `COMPOSE_PROJECT_NAME="$(basename "$SAAIO_REPO")-$SAAIO_FLOW_NAME"`
     (compose reads it from `.env`, so the worker's own `docker compose`
     commands reach the same stack) and URLs that carry a port
     (`APP_URL`). Two repos can have flows of the same name, which is why
     the project name carries the repo; lowercase it and turn anything but
     letters, digits, `-` and `_` into `-`, as compose accepts nothing
     else;
   - installs dependencies the way the README does (`composer install`,
     `npm ci`), inside a container when the project has no local tooling;
   - starts the stack (`docker compose up -d --wait`, or `sail up -d`),
     then migrates and seeds inside it;
   - starts no foreground dev server (setup has to return): the worker
     runs `npm run dev` itself, on the `VITE_PORT`/`PORT` in its `.env`;
   - ends by printing where the services answer, one line each.

5. **Write `.saaio/teardown`** when there is something to clean up (a
   project with only dev servers has none: removing the worktree removes
   its `.env`). From the worktree, stop and remove the
   stack with its volumes (`docker compose down -v --remove-orphans`, or
   `sail down -v`). It must not fail on a worktree whose setup failed
   halfway: guard each step so a missing `.env` or stack is not an error.

6. **Write `.saaio/pause` and `.saaio/resume`** when setup starts a stack
   (a project with only dev servers has none: the worker runs those
   itself). From the worktree:
   - pause: `docker compose stop` (or `sail stop`), keeping the containers,
     volumes and ports setup made;
   - resume: `docker compose up -d --no-recreate --wait` (or `sail up -d`),
     which starts the same containers and returns once they are healthy.
     Compose reads the ports and `COMPOSE_PROJECT_NAME` from the
     worktree's `.env`, so nothing is computed again.
   Both quiet, idempotent (pausing a stopped stack, resuming a running one
   succeed), and ending a failure with one line on stderr: saaio shows it
   on the flow.

7. **Make them executable.** `chmod +x` every script; saaio skips a hook
   that is not executable. `.gitignore` needs no change: saaio excludes
   `.saaio/worktrees/` itself.

8. **Prove it in a scratch worktree.** Use slot 20 (the one real flows
   reach last; with saaio installed, check `saaio status --all` and pick a
   free one): `git worktree add .saaio/worktrees/setup-saaio-check -b
   setup-saaio-check`, bring the uncommitted changes into it
   (`git diff HEAD | git -C <worktree> apply`), as a commit would, run
   `.saaio/setup` there with the five variables
   set, check that each service answers on its slot port (`curl` for
   HTTP, `nc -z` or a client for the rest) and that a stack already
   running in the main checkout is untouched. Run `.saaio/pause` and check
   the stack's containers are stopped, run it again, then `.saaio/resume`
   twice and check each service answers on the same port. Then run
   `.saaio/teardown`,
   check its containers and volumes are gone, and remove the worktree and
   branch (`git worktree remove --force`, `git branch -D`). Fix what
   fails and run it again. Without Docker running, say so and give the
   command to run the check later.

9. **Offer the branch convention.** If the project's rules
   (`CLAUDE.md`, `CONTRIBUTING.md`, the README) name a branch convention,
   offer `.saaio/config.toml`:
   ```toml
   [branch]
   name  = "{type}/{ticket}-{slug}"
   types = ["feature", "bugfix", "hotfix", "chore"]
   ```
   `{ticket}` is the request's ticket key, `{slug}` up to five words after
   it, `{name}` the flow's name; the first type is the default.

10. **Hand over.** List the files changed and the port table, and say
    what the dry run showed. Say that the compose change takes effect for
    flows once committed, and offer to commit it with the scripts (so the
    team gets them too). Commit when the user asks for a
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
- `.saaio/setup`: `HTTP_PORT=$((18080 + SAAIO_SLOT))`,
  `DB_PORT=$((13306 + SAAIO_SLOT))`, `.env` with those, `APP_URL` on the
  HTTP port and `COMPOSE_PROJECT_NAME=shop-<flow name>`;
  `docker compose up -d --wait`;
  `docker compose exec -T php php artisan migrate --seed --force`; prints
  `http://localhost:18083` and `mysql 127.0.0.1:13309` for slot 3;
- `.saaio/teardown`: `docker compose down -v --remove-orphans`;
- `.saaio/pause`: `docker compose stop`; `.saaio/resume`:
  `docker compose up -d --no-recreate --wait`.
