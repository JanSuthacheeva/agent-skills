I committed the merge on `main` as `6969f76 api: merge feature/invoice-currency`. I checked first and there were no conflict markers left.

Your resolution in `api/invoices.py` keeps the feature branch's version, so the invoice currency comes from `invoice.account.currency`. That means main's `request.args.get("currency", "USD")` is gone: callers can no longer pick the currency with a `currency` query parameter, and there's no USD default anymore. If that's what you meant, there's nothing else to do.

I haven't pushed and haven't run any tests.