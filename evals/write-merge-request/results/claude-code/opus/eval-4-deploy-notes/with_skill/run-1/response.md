I couldn't find a ticket ID in the branch name, so the title follows the repo's commit scopes. There's no MR template in the repo and no open MR for the branch.

---

**Title**

```
billing: upload invoice exports to s3
```

**Description**

```
Invoice exports outgrew the response timeout. They are now uploaded to an
S3 bucket, and each upload is recorded in a new `export_jobs` table.

Deploy:
- Before deploy: set `EXPORT_BUCKET`, `EXPORT_ACCESS_KEY_ID` and
  `EXPORT_SECRET_ACCESS_KEY` (required). `EXPORT_REGION` is optional and
  defaults to `eu-central-1`.
- Before deploy: create the bucket and an access key that can upload to it.
- Install the new dependency `boto3==1.35.0` from `requirements.txt`.
- Run migration `0007_add_export_jobs` (creates `export_jobs`).
```

---

Before you use this, check one thing. The commit message says "the user gets a link instead", but the code doesn't do that yet. This branch only adds `upload_export()` and the `export_jobs` table:
- Nothing calls `upload_export()`.
- Nothing writes rows to `export_jobs`.
- Nothing creates a link for the user.

So I left the link out of the description. If wiring it up is planned for a later MR, I can add a "follows later" line. If it should be in this MR, the branch is probably missing a commit.

Say so when you want me to push the branch and create the MR on GitLab.