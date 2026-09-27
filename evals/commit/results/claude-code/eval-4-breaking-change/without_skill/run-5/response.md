I committed the staged changes to `README.md` and `api/invoices.py` as `db94df5 api: invoices: drop currency query parameter`.

This is a breaking change, so the commit message has a `BREAKING CHANGE:` note. It says that `GET /invoices/<id>` no longer accepts the `currency` query parameter, and that clients should read `currency` from the response instead. The body also explains why: the parameter let clients label totals with a currency we never converted them to.

You asked me to always use the `/commit` skill, but it isn't in this session's skill list, so I wrote the message by hand. I followed the scope style already used in the history, as in `api: auth: ...`.