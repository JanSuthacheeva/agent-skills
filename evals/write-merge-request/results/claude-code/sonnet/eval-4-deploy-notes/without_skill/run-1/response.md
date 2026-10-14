**Title:** `billing: upload invoice exports to S3`

**Description:**

```markdown
## Why

Invoice exports outgrew the response timeout. They are now written to an S3 bucket so the user can get a link instead of waiting on the response.

## What

- Add `billing/export_s3.py` with `upload_export(path, key)`, which uploads a file to the export bucket with boto3.
- Add migration `0007_add_export_jobs` that creates an `export_jobs` table (`id`, `s3_key`, `created_at`) to track uploaded exports.
- Pin `boto3==1.35.0` in `requirements.txt`.
- Add the new `EXPORT_*` settings to `.env.example`.

## Deploy notes

- Set these env vars before deploying. `upload_export` reads the credentials and bucket with `os.environ[...]`, so a missing value raises `KeyError` on the first export.
  - `EXPORT_BUCKET`
  - `EXPORT_ACCESS_KEY_ID`
  - `EXPORT_SECRET_ACCESS_KEY`
  - `EXPORT_REGION` is optional and defaults to `eu-central-1`.
- Run migration `0007_add_export_jobs`. It only adds a new table, so it is safe to run before or after the code deploy. `down` drops `export_jobs` and its data.
- The bucket must exist, and the credentials need `s3:PutObject` on it.
- Install dependencies (`boto3`).

## Not included

- `upload_export` is not called from anywhere yet, and nothing writes to `export_jobs`. Wiring it into the export flow and returning the link to the user is not part of this branch.
```

Two things to check before you open the PR:
- The "Not included" section reflects what the diff shows. If the wiring lives in another branch, link it there or drop the section.
- The branch name `feature/export-to-s3` has no ticket ID, so I used a scoped-commit title. If there is a ClickUp ticket, the title should be `<ticket ID> <ticket title>` instead.