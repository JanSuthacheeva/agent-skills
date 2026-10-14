The merge is finished. It's commit `69027b6` on `main`, and I kept git's default message:

```
Merge branch 'feature/invoice-currency'

# Conflicts:
#	api/invoices.py
```

Only `api/invoices.py` was staged, and `git diff --check` found no leftover conflict markers.