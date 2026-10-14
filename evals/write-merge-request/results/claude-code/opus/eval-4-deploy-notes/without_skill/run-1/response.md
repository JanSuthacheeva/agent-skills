The branch name `feature/export-to-s3` has no ticket ID, so I used a Scoped Commits title. The remote is GitLab, so this is written as an MR.

---

**Title:** `billing: upload invoice exports to s3`

**Description:**

```markdown
## Summary

Adds a way to upload invoice export files to S3 and a table for tracking export jobs.

## Changes

- `billing/export_s3.py`: new `upload_export(path, key)` that uploads a local file to the configured S3 bucket using boto3.
- `migrations/0007_add_export_jobs.py`: new `export_jobs` table (`id`, `s3_key`, `created_at`).
- `requirements.txt`: adds `boto3==1.35.0`.
- `.env.example`: documents the new `EXPORT_*` variables.

## Deploy notes

Before deploying:

1. **Set these environment variables** in every environment:
   - `EXPORT_BUCKET` (required)
   - `EXPORT_ACCESS_KEY_ID` (required)
   - `EXPORT_SECRET_ACCESS_KEY` (required)
   - `EXPORT_REGION` (optional, defaults to `eu-central-1`)

   If any of the required variables is missing, `upload_export` raises `KeyError` when it is called.
2. **Run migration `0007_add_export_jobs`.** It creates the `export_jobs` table. Rolling back drops the table and any rows in it.
3. **Install dependencies.** `boto3==1.35.0` is new.

The S3 credentials need `s3:PutObject` on the export bucket.

## Testing

- [ ] Migration runs `up` and `down` cleanly
- [ ] `upload_export` uploads a file to a test bucket using the env config above
```

---

Before you open this MR:

- **Nothing uses this code yet.** No code calls `upload_export`, and nothing writes to `export_jobs`. If that's planned for a later MR, add a "Follow-ups" line to the description. If not, wiring them up probably belongs in this branch.
- **No tests.** The branch adds no tests, so the Testing section is a manual checklist. Edit it if you've already tested something.
- **Credentials.** The code reads static access keys from the environment. If the app runs on AWS, an IAM role (boto3's default credential chain) would let you remove `EXPORT_ACCESS_KEY_ID` and `EXPORT_SECRET_ACCESS_KEY` completely.

I haven't pushed anything or created the MR. I can do either if you want.