**Title:** `billing: upload invoice exports to S3`

---

## Summary

Invoice exports outgrew the response timeout. This adds an S3 upload helper so exports can be written to a bucket and the user gets a link instead. It also adds an `export_jobs` table to track uploaded exports.

## Changes

- `billing/export_s3.py`: new `upload_export(path, key)` that uploads a file to the export bucket with boto3.
- `migrations/0007_add_export_jobs.py`: creates `export_jobs` (`id`, `s3_key`, `created_at`). The down migration drops the table.
- `requirements.txt`: adds `boto3==1.35.0`.
- `.env.example`: documents the new env vars.

## Deploy notes

- **Env vars must be set before deploy.** `EXPORT_BUCKET`, `EXPORT_ACCESS_KEY_ID` and `EXPORT_SECRET_ACCESS_KEY` are read with `os.environ[...]`, so a missing value raises `KeyError` on the first upload. `EXPORT_REGION` is optional and defaults to `eu-central-1`.
- **Bucket and credentials needed.** The bucket must exist, and the IAM user needs at least `s3:PutObject` on it.
- **Migration:** run `0007_add_export_jobs` on deploy. It only creates a new table, so it is safe to run before the code ships. Rollback is the down migration, which drops the table and any rows in it.
- **Dependency:** `pip install -r requirements.txt` for boto3.

## Not included

Nothing in this diff calls `upload_export`, writes to `export_jobs`, or generates the link for the user. The change is inert until that wiring lands.

## Testing

No tests are included. I haven't run the upload against a real bucket.

---

Before you open the PR, you may want to confirm the "not included" part. If the wiring is meant to be in this PR, it's missing. If it's coming in a follow-up, link that here. I also left out any "tested against staging" claim because I have no evidence of it. Add one if it's true.