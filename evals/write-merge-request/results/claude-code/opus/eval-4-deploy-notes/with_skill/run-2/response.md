Here's the draft. There's no MR open for `feature/export-to-s3` yet, and I didn't find an MR template in the repo.

**Title**

```
billing: upload invoice exports to s3
```

**Description**

```
Invoice exports outgrew the response timeout. They are now uploaded to an
S3 bucket so the user can get a link instead of waiting for the file in
the response, and each upload is recorded in a new `export_jobs` table.

Deploy:
- Before deploy: create the export bucket and an access key that can write
  to it. Set `EXPORT_BUCKET`, `EXPORT_ACCESS_KEY_ID` and
  `EXPORT_SECRET_ACCESS_KEY` (required - the upload fails with a KeyError
  without them). `EXPORT_REGION` is optional and defaults to `eu-central-1`.
- Install the new dependency `boto3==1.35.0` from `requirements.txt`.
- Run migration `0007_add_export_jobs` (creates `export_jobs`).
```

I left out the "Review" section because the diff is only 22 lines.

Before you publish it, I noticed a gap between the branch and the commit message:
- **Nothing calls the new code yet.** No code calls `upload_export`, and nothing writes to `export_jobs`.
- **No link is created.** The commit says the user gets a link, but no code makes one (for example a presigned URL).

If this is meant to be the first part, I'd add a line saying the hookup into the export flow comes in a later MR. Otherwise the code that connects it is missing. Tell me which, and whether to push and create the MR.