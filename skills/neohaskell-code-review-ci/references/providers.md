# Provider setup

Use only the consumer's provider. The assets are templates for a trusted review pipeline; fill in the consumer-owned preparation and reviewer wrappers before enabling them. They deliberately do not choose a provider, model, API key name, or publication policy for the consumer.

The trusted preparation wrapper `.ci/prepare-review` receives base SHA, head SHA, and an output directory. Implement it to validate full SHAs, fetch those objects from the configured repository, write `patch.diff` with `git diff`, and collect the relevant source as inert text in `context.txt`. It must not check out or execute the head. The trusted `.ci/review` wrapper follows [the contract](review-contract.md) and uses the explicitly selected reviewer. Pin tool versions and action identities according to the consumer's CI policy.

Copy `scripts/` and the schema into the consumer's existing CI support directory, or use their installed `.agents/skills/neohaskell-code-review-ci/` paths. Adapt the asset paths to that choice. Keep these wrappers and parser on the trusted base revision, never the reviewed branch. Review includes related source even when findings cite changed lines.

| Provider | Asset | Trust and input setup |
|---|---|---|
| GitHub Actions | [github.yml](../assets/github.yml) | Uses `pull_request_target` only to run trusted base code. Keep permissions read-only, disable checkout credentials, and never execute the PR head. Base/head come from event metadata through environment variables. |
| GitLab CI | [gitlab.yml](../assets/gitlab.yml) | Run in a separately protected review pipeline/config ref. Pass validated base/head values from the MR API; fork pipelines must not receive protected secrets. |
| Azure DevOps | [azure.yml](../assets/azure.yml) | Use a trusted pipeline/template revision and a protected service connection. Resolve actual target/source commits from PR metadata before starting the job. |
| Bitbucket Pipelines | [bitbucket.yml](../assets/bitbucket.yml) | Run the custom review pipeline on the protected base ref. Supply base/head from verified PR metadata; do not run the PR branch's pipeline with reviewer credentials. |

The non-GitHub assets require `REVIEW_BASE_SHA` and `REVIEW_HEAD_SHA` to be supplied by that trusted launch. `REVIEW_API_KEY` is an adapter variable: the trusted reviewer wrapper maps it to the selected provider's API without logging it. Keep unrelated credentials out of this job.

Results stay as artifacts by default. If comment publication is requested, add a separate trusted publisher that accepts validated JSON and exact PR/head identity, escapes content, and receives only the scoped publication token. Do not send raw output to a shell or use a text search as a merge verdict. Use `FAIL_ON_BLOCKERS=true` only for an explicitly requested gate. Parser/runner failure remains a failed review in either mode.

After installation, the consumer can run `python3 -m unittest discover -s .agents/skills/neohaskell-code-review-ci/tests` and exercise a clean response, a real blocker, malformed output, and reviewer failure in its chosen CI. These are maintenance recipes, not claims that CI has already been installed or run.
