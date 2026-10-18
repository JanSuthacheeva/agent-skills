#!/usr/bin/env bash
# Build a throwaway project repo for one setup-saaio eval.
# Usage: setup_fixture.sh <eval-name> <dest-dir>
set -euo pipefail
name=$1; dest=$2
rm -rf "$dest"; mkdir -p "$dest/shop"; dest=$(cd "$dest" && pwd); cd "$dest/shop"
git init -q -b main
git config user.name "Eval User"; git config user.email "eval@example.com"
git config commit.gpgsign false
printf '.env\nnode_modules/\n' > .gitignore

case $name in
compose-hardcoded-ports)
  mkdir -p public
  echo '<h1>shop</h1>' > public/index.html
  cat > compose.yaml <<'Y'
services:
  web:
    image: nginx:alpine
    ports:
      - "8080:80"
    volumes:
      - ./public:/usr/share/nginx/html:ro
  cache:
    image: redis:7-alpine
    container_name: shop-redis
    ports:
      - "6379:6379"
Y
  printf 'APP_NAME=shop\nAPP_URL=http://localhost:8080\nREDIS_HOST=127.0.0.1\nREDIS_PORT=6379\n' > .env.example
  cp .env.example .env
  printf '# shop\n\n## Setup\n\n    cp .env.example .env\n    docker compose up -d\n\nThe site is on http://localhost:8080.\n' > README.md
  ;;
dev-server)
  cat > package.json <<'J'
{
  "name": "shop-web",
  "private": true,
  "scripts": { "dev": "node server.js" }
}
J
  cat > server.js <<'J'
const http = require("http");
const port = Number(process.env.PORT || 5173);
http.createServer((_, res) => res.end("shop-web\n")).listen(port, () => console.log(`http://localhost:${port}`));
J
  printf 'PORT=5173\n' > .env.example
  printf '# shop-web\n\n    npm run dev   # http://localhost:5173\n' > README.md
  ;;
sail-env)
  mkdir -p public vendor/bin
  echo '<h1>shop</h1>' > public/index.html
  cat > docker-compose.yml <<'Y'
services:
  laravel.test:
    image: nginx:alpine
    ports:
      - "${APP_PORT:-80}:80"
    volumes:
      - ./public:/usr/share/nginx/html:ro
  redis:
    image: redis:7-alpine
    ports:
      - "${FORWARD_REDIS_PORT:-6379}:6379"
Y
  cat > vendor/bin/sail <<'S'
#!/usr/bin/env bash
# A stand-in for Laravel Sail: the same commands, straight to docker compose.
exec docker compose "$@"
S
  chmod +x vendor/bin/sail
  printf '{\n  "name": "acme/shop",\n  "require-dev": { "laravel/sail": "^1.41" }\n}\n' > composer.json
  printf 'APP_NAME=shop\nAPP_URL=http://localhost\nAPP_PORT=80\nFORWARD_REDIS_PORT=6379\n' > .env.example
  cp .env.example .env
  printf '# shop\n\nLaravel Sail:\n\n    cp .env.example .env\n    vendor/bin/sail up -d\n' > README.md
  ;;
*) echo "unknown eval $name" >&2; exit 2 ;;
esac
git add -A; git commit -q -m "initial"
git rev-parse HEAD > "$dest/base_sha"
