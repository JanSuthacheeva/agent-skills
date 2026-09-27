I committed the staged changes on `ECOM-88-drop-currency-param` as `73bda1c`:

```
api: invoices: drop currency query parameter
```

The commit body explains why: clients could ask for totals in a currency we never converted to, so the amount and currency could disagree. It has a `BREAKING CHANGE:` note saying clients must stop sending `currency` and read it from the response instead. It also links the ticket with `Refs: ECOM-88`.

Your global instructions say to use the `/commit` skill, but no skill with that name is installed here. I followed the `git-conventions` skill and the scoped-commit format from your repo history instead.

Nothing has been pushed yet. Say "push" if you want it on the remote.