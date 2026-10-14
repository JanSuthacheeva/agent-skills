**Title**

```
billing: upload invoice exports to s3
```

**Description**

```
Invoice exports outgrew the response timeout, so they are written to an S3 bucket and the user gets a link instead. This adds the upload helper and an `export_jobs` table to track each export.

- `upload_export` is not called from anywhere yet, and nothing creates `export_jobs` rows or hands out the link. This MR only adds the pieces.

Deploy:
- Before deploy: create the export bucket and an IAM user that can write to it.
- Before deploy: set `EXPORT_BUCKET`, `EXPORT_ACCESS_KEY_ID` and `EXPORT_SECRET_ACCESS_KEY`. `EXPORT_REGION` defaults to `eu-central-1`. The upload fails with a `KeyError` if one of the three required variables is missing.
- With deploy: run migration `0007_add_export_jobs`. It creates a new table only, and `down` drops it.
- With deploy: install the new dependency `boto3==1.35.0`.
```

Notes:
- The branch name has no ticket ID, so the title is a scoped commit and there is no `Refs:` line.
- I left out the Review section because the diff is four small files.
- I left out the reasons for using a single IAM user and static keys, and for storing only `s3_key` and `created_at` in `export_jobs`, because I couldn't find them in the commits. If you have them, I can add them as decision bullets.
- The "not called from anywhere yet" bullet comes from the diff. If a follow-up MR wires it up, name it there.
- No MR is open for this branch, and the working tree is clean. Tell me when you want me to push and create it.