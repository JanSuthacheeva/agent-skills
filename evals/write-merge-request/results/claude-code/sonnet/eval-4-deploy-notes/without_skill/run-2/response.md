**Title:** `billing: upload invoice exports to S3`

(The branch name has no ticket ID, so this uses a scoped-commit title.)

**Description**

## What

Invoice exports can now be uploaded to S3. Each upload is tracked in a new `export_jobs` table.

## Changes

- `billing/export_s3.py`: new `upload_export(path, key)`. It builds a boto3 S3 client from env vars and uploads the file to the export bucket.
- `migrations/0007_add_export_jobs.py`: creates `export_jobs` with `id`, `s3_key` and `created_at`. The `down` step drops the table.
- `requirements.txt`: adds `boto3==1.35.0`.
- `.env.example`: documents the new config vars.

## Deploy notes

- Set these env vars in every environment before deploying:
  - `EXPORT_BUCKET` (required)
  - `EXPORT_ACCESS_KEY_ID` (required)
  - `EXPORT_SECRET_ACCESS_KEY` (required)
  - `EXPORT_REGION` (optional, defaults to `eu-central-1`)
- Run migration `0007` before the new code is used. It is a plain `CREATE TABLE`, so it is additive and rollback is `down`.
- Install the new dependency (`boto3`).
- If the bucket or credentials are missing, `upload_export` raises `KeyError`.

## Notes for reviewers

- `upload_export` is not called from anywhere yet. This branch adds only the uploader and the table.
- Nothing writes to `export_jobs` yet. The commit message says "track export jobs", but this diff only adds the table.
- No tests are included.
- Credentials come from static access keys in env vars. An IAM role would avoid that if the deployment environment supports one.

I haven't run the code or the migration.

Two things to check before opening the MR. If the uploader is meant to be wired into the export flow in this branch, that is missing. If a ticket exists, tell me the ID and I'll switch the title to `<ID> <ticket title>`.