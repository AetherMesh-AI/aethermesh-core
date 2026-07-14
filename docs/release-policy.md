# Desktop release policy

The Desktop Build and Numbered Prerelease workflow separates continuous build
artifacts from permanent releases.

- Every push to `main` validates and packages all four desktop targets, then keeps
  the installers as GitHub Actions artifacts for 14 days. It does not tag or
  create a GitHub Release.
- The weekly path targets Monday at 10:00 AM `America/New_York`. GitHub cron only
  accepts UTC, so the workflow runs at both possible UTC hours and continues only
  when the New York local time is exactly Monday 10:00. It skips publication when
  no commits exist after the latest numbered prerelease.
- A manual dispatch defaults to `main`. Leaving `publish_release` false performs
  the same artifact-only build. Setting it true requires the selected exact SHA
  to be reachable from `main`, all required checks for that SHA to be successful,
  and approval through the protected `release` environment.
- Scheduled and manual publishers share a non-cancelling concurrency group. In
  that serialized job they re-read remote tags and GitHub Releases, ignore legacy
  hash tags, and choose one more than the greatest `v0.2.0-alpha.<number>` tag.
  The first numeric build is 116. Existing tags are never moved or overwritten.
- Release notes list commits since the previous numbered prerelease. Validation,
  artifact-only, no-change, and unapproved runs never calculate or publish a tag.
  A collision fails safely and must be retried as a new serialized workflow run.

Repository administrators must configure an environment named `release` with
required reviewers before enabling manual promotion. Publish-scoped
`contents: write` permission exists only on the two publication jobs.