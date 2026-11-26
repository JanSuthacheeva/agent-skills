I fixed two security bugs on `feature/bookmark-share`. Both let a bookmark file shared by a colleague cause harm when you run `bm open` on one of its entries. All 16 tests pass.

## Fixed
- **Any URL scheme was accepted.** `parseWebUrl` let through `file:///etc/passwd`, `javascript:alert(1)` and `x:"; touch …; "`, though the plan allows only `http:` and `https:`. It now rejects everything else. `25a8275`, with tests at the URL level and for the `import` command.
- **Shell injection in `openUrl`.** It ran `execSync(\`${opener} "${url}"\`)`, so a URL from an imported file reached the shell. I created a file on disk through it. `https://a.dev/?$(…)` would also run, so the scheme fix alone doesn't close it. It now uses `execFileSync(opener, [url])`, as the plan says. `ae0e06e`, with a test that fails if the old line is put back.

A fresh agent reviewed both fixes and found no problems. I also added a `## Review` section to the plan (`88da878`).

## Open (your call)
- **Bad import files crash.** `bm import` on a missing file, invalid JSON or a non-array JSON value prints a raw stack trace. I'd map these to a clear message and exit 2, but the plan doesn't define this error, so I didn't add it.
- **Bad titles are saved.** A title that isn't text, such as `{"x":1}`, is written into the store file as-is. I'd reject such entries the same way bad URLs are rejected.
- **`bm add` doesn't check URLs**, so bookmarks added by hand can still use any scheme. The plan only requires the check on import. I'd add it to `add` too.
- **`BM_OPENER` can't take arguments now.** A value like `open -a Foo` no longer works. That matches the plan ("the command in BM_OPENER").

## Where to look
1. `src/opener.ts`: confirm nothing goes through a shell anymore.
2. `src/cli.ts`, the `import` case: how the untrusted file is parsed and validated.
3. `src/urls.ts`: the scheme check.

The store changes (`get`, `importAll`, and `add` now going through `importAll`) are routine and can be skimmed.

## Checks
- **Tests:** green at `88da878`. The project has no lint or type-check setup.
- **Security review:** `/security-review` ran on `main...HEAD` and reported the same two issues. Its own filter scored the scheme issue 7/10, below its cut-off of 8, but I proved it directly, so I fixed it anyway.

Nothing was pushed.