I committed the staged changes (`api/invoices.py` and `README.md`) as `4d58444` on `ECOM-88-drop-currency-param`:

```
api: invoices: drop currency query parameter
```

The body explains why the change was made. It also has a `BREAKING CHANGE:` note: `GET /invoices/<id>` no longer accepts the `currency` query parameter, so clients must stop sending it and read `currency` from the response instead.

Your instructions say to use a `/commit` skill, but it isn't installed here. I wrote the message by hand in the `<scope>: <description>` format used in this repo's history, with the scope nested as in `api: auth: validate token expiry`.

I haven't pushed. Tell me "push" if you want it on the remote.