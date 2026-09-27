The three changes had nothing to do with each other, so I made three separate commits. The working tree is now clean.

- `a2ca5dc billing: round invoice totals half-even` - invoice totals now round half-to-even instead of half-up.
- `3bb000e worker: raise export retries to 5` - the export worker now retries 5 times instead of 3.
- `ef63bf6 docs: describe service in readme` - added a one-line description of the service to the README.

Your instructions say to use the `/commit` skill, but it isn't installed in this session, so I committed with plain git in the `<scope>: <description>` format.