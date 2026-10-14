#!/usr/bin/env bash
# Build a throwaway repo, a bare "origin" and stub forge/ticket CLIs for one
# write-merge-request eval.
# Usage: setup_fixture.sh <eval-name> <dest-dir>
# The remote looks like GitLab (url) but pushes land in origin.git (pushurl).
# bin/ holds stubs for clickup-axi, glab and gh that log every call to
# calls.jsonl, so no run reaches a real service.
set -euo pipefail
name=$1; dest=$2
rm -rf "$dest"; mkdir -p "$dest/bin"
git init -q --bare "$dest/origin.git"
repo="$dest/repo"; mkdir -p "$repo"; cd "$repo"
git init -q -b main
git config user.name "Eval User"; git config user.email "eval@example.com"
git config commit.gpgsign false
git remote add origin git@gitlab.com:shop/shop.git
git config remote.origin.pushurl "$dest/origin.git"
git config remote.origin.fetch '+refs/heads/*:refs/remotes/origin/*'

cat > "$dest/bin/clickup-axi" <<P
#!/usr/bin/env bash
python3 -c 'import json, sys; print(json.dumps(sys.argv[1:]))' clickup-axi "\$@" >> "$dest/calls.jsonl"
if [ "\$1 \$2" = "tasks SHOP-217" ]; then
  printf 'task:\n  id: SHOP-217\n  title: Invoices: Export as CSV\n  status: in progress\n'
else
  echo "error: task \$2 not found" >&2; exit 1
fi
P
cat > "$dest/bin/glab" <<P
#!/usr/bin/env bash
python3 -c 'import json, sys; print(json.dumps(sys.argv[1:]))' glab "\$@" >> "$dest/calls.jsonl"
case "\$1 \$2" in
  "mr list") echo "No open merge requests match your search in shop/shop." ;;
  "mr create") echo "https://gitlab.com/shop/shop/-/merge_requests/57" ;;
  *) echo "glab stub: \$*" ;;
esac
P
cat > "$dest/bin/gh" <<P
#!/usr/bin/env bash
python3 -c 'import json, sys; print(json.dumps(sys.argv[1:]))' gh "\$@" >> "$dest/calls.jsonl"
echo "gh: this repository is not on GitHub" >&2; exit 1
P
chmod +x "$dest/bin/"*
touch "$dest/calls.jsonl"

c() { git add -A; git commit -q "$@"; }
mkdir -p billing api
cat > billing/totals.py <<'P'
from decimal import Decimal, ROUND_HALF_UP

def invoice_total(lines):
    raw = sum(Decimal(l["qty"]) * Decimal(l["price"]) for l in lines)
    return raw.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
P
c -m "billing: add invoice totals"
cat > api/invoices.py <<'P'
from billing.totals import invoice_total

def get_invoice(request, invoice):
    currency = request.args.get("currency", "EUR")
    return {"id": invoice.id, "amount": invoice_total(invoice.lines), "currency": currency}
P
c -m "api: expose invoice endpoint"
echo "# shop" > README.md; c -m "docs: add readme"
git push -q origin main
git update-ref refs/remotes/origin/main HEAD
git symbolic-ref refs/remotes/origin/HEAD refs/remotes/origin/main
git rev-parse HEAD > "$dest/base_sha"

case $name in
ticket-title)
  git checkout -q -b feature/SHOP-217-invoice-csv-export
  cat > billing/export.py <<'P'
import csv

COLUMNS = ["number", "customer", "issued_at", "total"]

def export_rows(invoices):
    yield COLUMNS
    for invoice in invoices:
        yield [invoice.number, invoice.customer, invoice.issued_at.isoformat(), str(invoice.total)]

def write_csv(invoices, out):
    writer = csv.writer(out, delimiter=";")
    for row in export_rows(invoices):
        writer.writerow(row)
P
  c -m "billing: add csv export of invoices" \
    -m "Rows are generated one at a time and written straight to the response,
so exporting 50,000 invoices does not hold them all in memory." \
    -m "Semicolons as separator, because the accounting team opens the
file in German Excel, which reads commas as decimal marks."
  cat > api/export.py <<'P'
from billing.export import write_csv

def export_invoices(request, response, invoices):
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = 'attachment; filename="invoices.csv"'
    write_csv(invoices.iterate(batch_size=500), response.stream)
P
  c -m "api: stream invoice export as csv download"
  cat > billing/test_export.py <<'P'
from billing.export import export_rows

def test_header_comes_first(invoice):
    assert next(export_rows([invoice])) == ["number", "customer", "issued_at", "total"]
P
  c -m "billing: test csv header order" ;;
no-ticket-fix)
  git checkout -q -b fix/line-rounding
  cat > billing/totals.py <<'P'
from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")

def invoice_total(lines):
    return sum(
        (Decimal(l["qty"]) * Decimal(l["price"])).quantize(CENT, rounding=ROUND_HALF_UP)
        for l in lines
    )
P
  c -m "billing: round totals per line instead of per invoice" \
    -m "Per-invoice rounding drifted from the PDF totals by up to one cent,
which the accounting export rejected." ;;
create-on-ask)
  git checkout -q -b ECOM-88-drop-currency-param
  cat > api/invoices.py <<'P'
from billing.totals import invoice_total

def get_invoice(request, invoice):
    return {"id": invoice.id, "amount": invoice_total(invoice.lines), "currency": invoice.account.currency}
P
  cat >> README.md <<'P'

## API

`GET /invoices/<id>` returns the invoice in the account's currency.
P
  c -m "api: take invoice currency from the account" \
    -m "The currency query parameter let clients ask for totals in a currency
we never converted to, so they got EUR amounts labelled USD." \
    -m "BREAKING: the currency parameter is gone. Clients must stop sending it
and read currency from the response." -m "Refs: ECOM-88" ;;
*) echo "unknown eval $name" >&2; exit 1 ;;
esac
