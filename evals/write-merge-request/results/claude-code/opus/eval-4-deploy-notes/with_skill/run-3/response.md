No open MR exists for `feature/export-to-s3`, and the repo has no MR template. Here's the draft:

---

**Title**

```
billing: upload invoice exports to s3
```

**Description**

```
Invoice exports have grown too big to finish before the response timeout.
Instead, they are written to an S3 bucket and the user gets a link. This MR
adds the upload helper and an `export_jobs` table that records each upload.

Deploy:
- Before deploy: set `EXPORT_BUCKET`, `EXPORT_ACCESS_KEY_ID` and
  `EXPORT_SECRET_ACCESS_KEY` (required, read with `os.environ[...]`).
  `EXPORT_REGION` is optional and defaults to `eu-central-1`.
- Before deploy: create the bucket and give the access key write access to it.
- Install the new dependency `boto3==1.35.0`.
- Run migration `0007_add_export_jobs` (creates `export_jobs`).
```

---

There's one thing to check before you push. The diff doesn't call `upload_export` from anywhere, nothing writes to `export_jobs`, and no link is generated (for example a presigned URL). That means the "user gets a link" part from the commit message isn't in this branch yet. If that wiring is meant to come in a later MR, I'd add a line like "Wiring the export flow to this helper and returning the link follows in a separate MR." If it should be in this MR, the branch looks incomplete. Which is it?

I didn't add a review guide because the diff is only 22 lines. When you want it pushed and the MR created, just say so.