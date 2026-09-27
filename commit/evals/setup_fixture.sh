#!/usr/bin/env bash
# Build a throwaway git repo (plus bare "origin") for one commit-skill eval.
# Usage: setup_fixture.sh <eval-name> <dest-dir>
set -euo pipefail
name=$1; dest=$2
rm -rf "$dest"; mkdir -p "$dest"
git init -q --bare "$dest/origin.git"
repo="$dest/repo"; mkdir -p "$repo"; cd "$repo"
git init -q -b main
git config user.name "Eval User"; git config user.email "eval@example.com"
git config commit.gpgsign false
git remote add origin "$dest/origin.git"

# c <scoped message> [conventional message]: conventional-history builds the
# same tree with a Conventional Commits log, no-scope-history with plain
# capitalized messages that carry no scope at all.
c() {
  git add -A
  msg=$1
  if [ "$name" = conventional-history ] && [ -n "${2:-}" ]; then msg=$2
  elif [ "$name" = no-scope-history ]; then
    msg=$(echo "$1" | sed -E 's/^.*: //' | awk '{print toupper(substr($0,1,1)) substr($0,2)}')
  fi
  git commit -q -m "$msg"
}
mkdir -p billing api worker
cat > billing/totals.py <<'P'
from decimal import Decimal, ROUND_HALF_UP

def invoice_total(lines):
    raw = sum(Decimal(l["qty"]) * Decimal(l["price"]) for l in lines)
    return raw.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
P
c "billing: add invoice totals" "feat(billing): add invoice totals"
cat > api/invoices.py <<'P'
from billing.totals import invoice_total

def get_invoice(request, invoice):
    currency = request.args.get("currency", "EUR")
    return {"id": invoice.id, "amount": invoice_total(invoice.lines), "currency": currency}
P
c "api: expose invoice endpoint" "feat(api): expose invoice endpoint"
cat > worker/export.py <<'P'
import time

def export(invoice, client, retries=3):
    for attempt in range(retries):
        try:
            return client.send({"amount": invoice.amount})
        except ConnectionError:
            time.sleep(1)
    raise RuntimeError("export failed")
P
cat > worker/test_export.py <<'P'
from worker.export import export

def test_export_retries(fake_client):
    fake_client.fail_times(2)
    assert export(fake_invoice(), fake_client)
P
c "worker: retry failed exports" "fix(worker): retry failed exports"
cat > api/auth.py <<'P'
import time

def token_valid(token, now=None):
    now = now or time.time()
    return token["exp"] > now
P
c "api: auth: validate token expiry" "feat(auth): validate token expiry"
echo "# shop" > README.md; c "docs: add readme" "docs: add readme"
echo "python 3.12" > .tool-versions; c "treewide: bump python to 3.12" "chore: bump python to 3.12"
git push -q origin main
git rev-parse HEAD > "$dest/base_sha"

case $name in
staged-ticket-branch)
  git checkout -q -b HGAI-3187-token-clock-skew
  cat > api/auth.py <<'P'
import time

# Mobile clients drift by up to a minute; without leeway their fresh
# tokens are rejected as expired.
CLOCK_SKEW_LEEWAY = 60

def token_valid(token, now=None):
    now = now or time.time()
    return token["exp"] + CLOCK_SKEW_LEEWAY > now
P
  git add api/auth.py ;;
nothing-staged-mixed)
  git checkout -q -b feature/export-backoff
  cat > worker/export.py <<'P'
import time

def export(invoice, client, retries=5, base_delay=0.5):
    for attempt in range(retries):
        try:
            return client.send({"amount": invoice.amount})
        except ConnectionError:
            time.sleep(base_delay * 2 ** attempt)
    raise RuntimeError("export failed")
P
  cat >> worker/test_export.py <<'P'

def test_export_backs_off_exponentially(fake_client, sleeps):
    fake_client.fail_times(3)
    export(fake_invoice(), fake_client)
    assert sleeps == [0.5, 1.0, 2.0]
P
  printf 'DEBUG dump of client payloads\n{"amount": 12.3}\n' > debug_dump.txt
  printf 'TODO: ask ops about retry ceiling\n' > notes.md ;;
push-multi-scope)
  sed -i '' 's/"amount": invoice_total(invoice.lines)/"amount_cents": int(invoice_total(invoice.lines) * 100)/' api/invoices.py
  sed -i '' 's/{"amount": invoice.amount}/{"amount_cents": int(invoice.amount * 100)}/' worker/export.py
  git add api/invoices.py worker/export.py ;;
breaking-change)
  git checkout -q -b ECOM-88-drop-currency-param
  cat > api/invoices.py <<'P'
from billing.totals import invoice_total

def get_invoice(request, invoice):
    # Currency now always comes from the owning account; the query
    # parameter let clients request totals in a currency we never converted to.
    return {"id": invoice.id, "amount": invoice_total(invoice.lines), "currency": invoice.account.currency}
P
  cat >> README.md <<'P'

## API

`GET /invoices/<id>` returns the invoice in the account's currency.
The `currency` query parameter was removed; clients that sent it must drop it
and read `currency` from the response instead.
P
  git add api/invoices.py README.md ;;
revert-default-message) ;;
merge-default-message)
  git checkout -q -b feature/invoice-currency
  sed -i '' 's/request.args.get("currency", "EUR")/invoice.account.currency/' api/invoices.py
  git commit -qam "api: take invoice currency from the account"
  git checkout -q main
  sed -i '' 's/request.args.get("currency", "EUR")/request.args.get("currency", "USD")/' api/invoices.py
  git commit -qam "api: default invoice currency to usd"
  git merge -q feature/invoice-currency >/dev/null 2>&1 || true
  cat > api/invoices.py <<'P'
from billing.totals import invoice_total

def get_invoice(request, invoice):
    currency = invoice.account.currency
    return {"id": invoice.id, "amount": invoice_total(invoice.lines), "currency": currency}
P
  git add api/invoices.py ;;
mixed-unrelated)
  git checkout -q -b feature/invoice-pagination
  cat > api/invoices.py <<'P'
from billing.totals import invoice_total

PAGE_SIZE = 50

def get_invoice(request, invoice):
    currency = request.args.get("currency", "EUR")
    return {"id": invoice.id, "amount": invoice_total(invoice.lines), "currency": currency}

def list_invoices(request, invoices):
    page = int(request.args.get("page", 1))
    start = (page - 1) * PAGE_SIZE
    return {"page": page, "items": [i.id for i in invoices[start:start + PAGE_SIZE]]}
P
  cat > api/test_invoices.py <<'P'
from api.invoices import list_invoices, PAGE_SIZE

def test_second_page_starts_after_first(fake_request, invoices):
    body = list_invoices(fake_request(page=2), invoices)
    assert body["items"][0] == invoices[PAGE_SIZE].id
P
  sed -i '' 's/            time.sleep(1)/            # WIP: try jitter here, not done yet\n            time.sleep(1)/' worker/export.py ;;
conventional-history)
  sed -i '' 's/            time.sleep(1)/            time.sleep(1 + random.random())/; s/^import time$/import random\nimport time/' worker/export.py
  git add worker/export.py ;;
treewide)
  for f in billing/totals.py api/invoices.py api/auth.py worker/export.py worker/test_export.py; do
    printf '# SPDX-License-Identifier: MIT\n%s\n' "$(cat "$f")" > "$f"
  done
  printf '\n## License\n\nMIT\n' >> README.md
  printf 'MIT License\n' > LICENSE
  git add -A ;;
no-scope-history)
  cat > api/auth.py <<'P'
import time

# Mobile clients drift by up to a minute; without leeway their fresh
# tokens are rejected as expired.
CLOCK_SKEW_LEEWAY = 60

def token_valid(token, now=None):
    now = now or time.time()
    return token["exp"] + CLOCK_SKEW_LEEWAY > now
P
  git add api/auth.py ;;
split-unrelated)
  sed -i '' 's/ROUND_HALF_UP/ROUND_HALF_EVEN/g' billing/totals.py
  sed -i '' 's/retries=3/retries=5/' worker/export.py
  printf '# shop\n\nInvoicing service: billing, API and export worker.\n' > README.md ;;
*) echo "unknown eval $name" >&2; exit 1 ;;
esac
