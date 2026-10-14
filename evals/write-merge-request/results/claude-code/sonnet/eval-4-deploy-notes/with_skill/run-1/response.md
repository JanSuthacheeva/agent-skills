**Title**

```
billing: upload invoice exports to s3
```

**Description**

```
Invoice exports outgrew the response timeout, so they are written to an S3 bucket and the user gets a link instead. This adds the upload helper and an `export_jobs` table that records each uploaded export's key.

Deploy:
- Before deploy: set `EXPORT_BUCKET`, `EXPORT_ACCESS_KEY_ID` and `EXPORT_SECRET_ACCESS_KEY`. `upload_export` reads them with `os.environ[...]`, so it raises `KeyError` if they are missing. `EXPORT_REGION` is optional and defaults to `eu-central-1`.
- Before deploy: the bucket must exist and the key must be allowed to write to it.
- With deploy: run migration `0007_add_export_jobs` (new table, no backfill). `boto3==1.35.0` is a new dependency, so reinstall requirements.
```

Notes:
- I did not run the push or `glab mr create`. Tell me if you want me to create it.
- The branch name has no ticket ID, so I used a scoped title and left out `Refs:`.
- The diff only uploads the file and creates the table. Nothing writes to `export_jobs` or builds the link for the user yet. If that follows in another MR, add a line saying so. I left it out because I can't tell from the branch.
- I left out Review and decision bullets because the change is small.
- There are no uncommitted changes and no open MR for this branch.