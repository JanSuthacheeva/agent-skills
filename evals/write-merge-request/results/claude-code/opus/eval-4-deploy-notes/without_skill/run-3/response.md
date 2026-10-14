Here's the draft. The remote is GitLab, so I wrote it as an MR. The branch name has no ticket ID, so the title uses the scoped-commit format.

---

**Title:** `billing: upload invoice exports to S3`

**Description:**

```markdown
## Why

Invoice exports have grown past the response timeout. Instead of returning the file in the response, we write it to an S3 bucket and give the user a link.

## What

- `billing/export_s3.py`: new `upload_export(path, key)`, which uploads a local export file to the bucket set in `EXPORT_BUCKET`.
- `migrations/0007_add_export_jobs.py`: new `export_jobs` table (`id`, `s3_key`, `created_at`) to track uploaded exports.
- Adds `boto3==1.35.0` to `requirements.txt`.
- Adds `.env.example` with the new export settings.

## Deploy notes

Do these before or along with the deploy:

1. **Set the new env vars** in every environment:
   - `EXPORT_BUCKET` - required
   - `EXPORT_ACCESS_KEY_ID` - required
   - `EXPORT_SECRET_ACCESS_KEY` - required
   - `EXPORT_REGION` - optional, defaults to `eu-central-1`

   If any required var is missing, `upload_export` raises `KeyError` when it's called.
2. **Set up the bucket** and an IAM user/key that has at least `s3:PutObject` on it.
3. **Install dependencies**: `boto3` is new.
4. **Run migration `0007_add_export_jobs`**. It's additive (one new table). Rollback drops `export_jobs`.

## Testing

- [ ] Run the migration up and down against a local DB
- [ ] Call `upload_export` against a test bucket and check the object is there
```

---

Some gaps came up while I was reading the diff. You may want to fix them before opening the MR, or say in the description that they're follow-ups:

- **The upload isn't connected to anything yet.** Nothing calls `upload_export`, and nothing writes rows to `export_jobs`. As the code stands, the timeout described under "Why" isn't fixed.
- **There's no link for the user.** The commit message says the user gets a link, but no code generates one (for example a presigned URL).
- **No tests are included.** The checklist above is manual only.

If these are planned for a later MR, I can reword "Why" so it doesn't promise the user-facing fix.