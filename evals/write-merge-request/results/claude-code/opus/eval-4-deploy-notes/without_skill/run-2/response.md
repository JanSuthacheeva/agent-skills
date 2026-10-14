I've drafted the description below; it isn't posted anywhere yet. The remote is GitLab, so it's written as a merge request. The branch name has no ticket ID, so the title uses the `scope: description` format.

---

**Title:** `billing: upload invoice exports to S3`

**Description:**

```markdown
## What

Adds the building blocks for writing invoice exports to S3 rather than returning them in the HTTP response.

- `billing/export_s3.py`: `upload_export(path, key)` uploads a local export file to the configured bucket.
- `migrations/0007_add_export_jobs.py`: new `export_jobs` table (`id`, `s3_key`, `created_at`) to track uploaded exports.
- `requirements.txt`: adds `boto3==1.35.0`.
- `.env.example`: documents the new `EXPORT_*` settings.

## Why

Exports outgrew the response timeout. Writing them to a bucket and giving the user a link avoids the timeout.

## Not in this MR

- Nothing calls `upload_export` yet, and nothing writes rows to `export_jobs`.
- Download links for users (e.g. presigned URLs) are not generated yet.

## Deploy notes

1. **Provision the bucket**: create the export bucket (default region `eu-central-1`) and an IAM user/role that can `s3:PutObject` to it.
2. **Set env vars** in every environment before deploying:
   - `EXPORT_BUCKET` (required)
   - `EXPORT_ACCESS_KEY_ID` (required)
   - `EXPORT_SECRET_ACCESS_KEY` (required)
   - `EXPORT_REGION` (optional, defaults to `eu-central-1`)
   The required vars are read with `os.environ[...]`, so a missing one raises `KeyError` when an upload runs.
3. **Install dependencies**: `boto3` is new, so rebuild the image or reinstall `requirements.txt`.
4. **Run migration** `0007_add_export_jobs`. It only creates a new table, so it's safe to run before the code goes out. To roll back, drop the table with `down`.

## Testing

- [ ] Migration runs up and down cleanly
- [ ] `upload_export` uploads a file to a test bucket using the configured credentials
```

---

Things to check before you open it:

- **Not wired up:** nothing in the repo calls `upload_export` and nothing writes to `export_jobs`, so this branch has no visible effect for users yet. I said so in the description; if the call site was supposed to be in this branch, it's missing.
- **No tests:** there are none for the new code, so the Testing checklist is a suggestion rather than something that was run.
- **Credentials:** the code reads the S3 access keys from env vars. If you deploy on AWS, you could rely on an IAM role instead and drop those two vars.

Do you want me to open the MR with this?