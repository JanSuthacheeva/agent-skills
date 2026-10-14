Title: no ticket ID in the branch name, so a scoped commit title.

**Title**
```
billing: upload invoice exports to S3
```

**Description**
```
Invoice exports outgrew the response timeout, so they are now uploaded to an S3 bucket and the user gets a link instead of a direct download. This MR adds the upload and the table that tracks export jobs.

- Credentials come from dedicated `EXPORT_*` variables instead of the app's default AWS credentials, so access can be scoped to the export bucket only.

Deploy:
- Before deploy: create the export bucket and set `EXPORT_BUCKET`, `EXPORT_ACCESS_KEY_ID` and `EXPORT_SECRET_ACCESS_KEY`. These are required; the upload raises a `KeyError` without them. `EXPORT_REGION` is optional and defaults to `eu-central-1`.
- Run migration `0007_add_export_jobs`, which creates the `export_jobs` table. It is a new table, so it is safe to run before the code goes out.
- Install the new dependency `boto3==1.35.0` (`requirements.txt`).

Not included: nothing calls `upload_export` or writes to `export_jobs` yet, and no download link is produced. The caller follows separately.
```

Notes:
- I left out the reason for the dedicated `EXPORT_*` credentials, since the commits don't state one. The bullet above is my inference, so confirm or delete it.
- "The caller follows separately" is also from the diff, which has no caller. Adjust it if that is wrong.
- Nothing is pushed and no MR exists yet. Tell me when to push and create it.