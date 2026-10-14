I committed the staged changes as `aef96f3`:

```
api: drop currency query param from invoice endpoint
```

- **Breaking change:** the message body has a `BREAKING CHANGE:` note. It says clients must stop sending `currency` and read it from the response instead.
- **Ticket:** I added a `Refs: ECOM-88` trailer, taken from the branch name.

Your instructions say to always use the `/commit` skill, but it isn't installed in this environment. I wrote the commit by hand in the same scope format as the existing history.