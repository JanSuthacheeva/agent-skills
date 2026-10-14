I committed the staged changes as `c025622` on `ECOM-88-drop-currency-param`:

```
api: invoices: drop currency query parameter
```

The commit body explains the reason: the parameter let clients label amounts with a currency we never converted to. It also has a `BREAKING CHANGE:` footer saying `GET /invoices/<id>` no longer accepts `currency`, so clients must read it from the response instead. The commit covers `api/invoices.py` and the README note.

Your instructions say to use the `/commit` skill, but it isn't installed in this session. I wrote the commit by hand, using the `api: auth:` scope style from your existing history.