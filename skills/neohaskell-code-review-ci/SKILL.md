---
name: neohaskell-code-review-ci
description: >-
  Scaffolds the CI pipeline file that runs neohaskell-code-review on every
  pull request or merge request without any third-party review SaaS. Use when
  setting up automated PR review for a NeoHaskell project, when asked to wire
  code review into CI, or when neohaskell-code-review needs to run headlessly
  in GitHub Actions, GitLab CI, Azure DevOps, or Bitbucket Pipelines.
  Auto-detects the CI provider from the repo layout (.github/ directory for
  GitHub Actions, .gitlab-ci.yml for GitLab CI, azure-pipelines.yml for Azure
  DevOps, bitbucket-pipelines.yml for Bitbucket Pipelines) and emits the
  native pipeline config. Documents required secrets (ANTHROPIC_API_KEY) and
  PR-write permissions for each provider. This is a one-time setup skill; it
  does not run on every commit. No third-party review SaaS is involved.
metadata:
  model: sonnet
---

**This is NeoHaskell, not vanilla Haskell.** The `.hs` extension is shared between them — the CI pipeline you are wiring here reviews NeoHaskell source, which uses `import Core` (not Prelude), `Task` (not `IO`), and the custom trap table. The upstream `neohaskell-code-review` skill knows all of this; your job here is purely CI plumbing.

In Claude Code this skill runs inline at Sonnet tier. In Cursor or Codex the `metadata.model` is advisory; the template generation is straightforward enough to run in any host.

---

## Inputs / Outputs / Next

- **Input:** the project root (to auto-detect the CI provider) + answers to three questions: (1) should the job post inline PR comments, post a summary comment, or summary-only? (2) should it fail the check on any blocker finding? (3) is there a non-default base branch (default: `main`)?
- **Output:** one provider-native pipeline file, a required-secrets checklist, and a permissions setup note.
- **Next:** — (this is a one-time setup; `neohaskell-code-review` handles the ongoing per-PR review logic).

---

## Step 1 — Detect the CI provider

Check which of these exists in the project root:

| Path present | Provider |
|---|---|
| `.github/` directory | GitHub Actions |
| `.gitlab-ci.yml` file | GitLab CI |
| `azure-pipelines.yml` file | Azure DevOps |
| `bitbucket-pipelines.yml` file | Bitbucket Pipelines |
| None of the above | Ask the user which provider they use |

Emit only the template for the detected provider. Do not emit all four; that creates confusion.

---

## Step 2 — Required secrets and permissions

Before writing the pipeline file, tell the user exactly what to add. The list is short and non-negotiable:

**Every provider:**

| Secret | Where to add | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | CI project secrets / repository secrets | Authenticates `claude` to the Anthropic API |

**Provider-specific tokens and permissions** — see the Per-Provider Setup note in each template below. GitHub Actions uses the built-in `GITHUB_TOKEN` with `pull-requests: write` in the workflow file; GitLab, Azure DevOps, and Bitbucket each need an additional personal-access token or pipeline variable with comment-post scope.

---

## Step 3 — Emit the pipeline template

Pick the matching section. Every template follows the same logic:

1. Trigger on PR/MR open and update.
2. Checkout with **full history** (`fetch-depth: 0` or equivalent) — the diff requires both base and head commits.
3. Install Node.js and `@anthropic-ai/claude-code`.
4. Compute the diff between base and head into a file.
5. Build a prompt referencing `neohaskell-code-review` and pipe the diff into `claude -p`.
6. Post the review output as a PR/MR comment via the provider API.
7. Exit non-zero if the review output contains the word "blocker" and `FAIL_ON_BLOCKERS` is true.

---

### Template A — GitHub Actions

File: `.github/workflows/neohaskell-review.yml`

Per-Provider Setup: `GITHUB_TOKEN` is automatically injected by Actions. Add `pull-requests: write` permission in the workflow (shown below). No extra token is needed. Add `ANTHROPIC_API_KEY` under **Settings → Secrets and variables → Actions → Repository secrets**.

```yaml
name: NeoHaskell Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

# GITHUB_TOKEN needs pull-requests: write to post a comment.
permissions:
  contents: read
  pull-requests: write

env:
  # Set to "false" to post the review but never fail the check.
  FAIL_ON_BLOCKERS: "true"

jobs:
  neohaskell-review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout (full history for diff)
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Install Claude Code
        run: npm install -g @anthropic-ai/claude-code

      - name: Compute diff
        run: |
          git diff \
            "${{ github.event.pull_request.base.sha }}" \
            "${{ github.event.pull_request.head.sha }}" \
            > /tmp/pr.diff

      - name: Run neohaskell-code-review
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          cat > /tmp/prompt.txt << 'PROMPT'
          Run the neohaskell-code-review skill on the diff below.
          Emit severity-ranked findings (blocker/major/minor/nit) with
          file:line citations and a concrete fix for each, then a one-line
          verdict.

          PROMPT
          cat /tmp/pr.diff >> /tmp/prompt.txt
          claude -p "$(cat /tmp/prompt.txt)" > /tmp/review.txt

      - name: Post review comment
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          BODY=$(cat /tmp/review.txt)
          gh pr comment "${{ github.event.pull_request.number }}" \
            --repo "${{ github.repository }}" \
            --body "## NeoHaskell Code Review

          ${BODY}"

      - name: Fail on blockers
        if: env.FAIL_ON_BLOCKERS == 'true'
        run: |
          if grep -qi "blocker" /tmp/review.txt; then
            echo "Blocker-severity findings detected. Failing the check."
            exit 1
          fi
```

---

### Template B — GitLab CI

File: append a new job to `.gitlab-ci.yml`

Per-Provider Setup: create a **Project Access Token** (or personal token) with `api` scope. Add it as a CI/CD variable named `GITLAB_TOKEN` (masked, protected). Also add `ANTHROPIC_API_KEY` as a masked variable. GitLab provides `CI_PROJECT_ID` and `CI_MERGE_REQUEST_IID` automatically.

```yaml
neohaskell-review:
  stage: test
  image: node:20-slim
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  variables:
    GIT_DEPTH: "0"
    FAIL_ON_BLOCKERS: "true"
  script:
    - apt-get update -qq && apt-get install -y -qq git curl python3
    - npm install -g @anthropic-ai/claude-code

    # Full history is required for the diff.
    - git fetch origin "$CI_MERGE_REQUEST_TARGET_BRANCH_NAME"
    - git diff "origin/${CI_MERGE_REQUEST_TARGET_BRANCH_NAME}...${CI_COMMIT_SHA}"
        > /tmp/pr.diff

    - |
      cat > /tmp/prompt.txt << 'PROMPT'
      Run the neohaskell-code-review skill on the diff below.
      Emit severity-ranked findings (blocker/major/minor/nit) with
      file:line citations and a concrete fix for each, then a one-line verdict.

      PROMPT
      cat /tmp/pr.diff >> /tmp/prompt.txt
      claude -p "$(cat /tmp/prompt.txt)" > /tmp/review.txt

    # Post as an MR note (comment).
    - |
      BODY=$(cat /tmp/review.txt | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))")
      curl --silent --fail-with-body \
        --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
        --header "Content-Type: application/json" \
        --data "{\"body\": ${BODY}}" \
        "${CI_SERVER_URL}/api/v4/projects/${CI_PROJECT_ID}/merge_requests/${CI_MERGE_REQUEST_IID}/notes"

    - |
      if [ "$FAIL_ON_BLOCKERS" = "true" ] && grep -qi "blocker" /tmp/review.txt; then
        echo "Blocker-severity findings detected. Failing the check."
        exit 1
      fi
```

---

### Template C — Azure DevOps

File: add a stage to `azure-pipelines.yml`

Per-Provider Setup: enable **Allow scripts to access the OAuth token** in the pipeline's Agent job settings (or set `persistCredentials: true` in the checkout step). This makes `$(System.AccessToken)` available, which has comment-post scope on the current PR. Add `ANTHROPIC_API_KEY` as a secret pipeline variable.

```yaml
stages:
  - stage: NeoHaskellReview
    displayName: NeoHaskell Code Review
    condition: eq(variables['Build.Reason'], 'PullRequest')
    variables:
      FAIL_ON_BLOCKERS: "true"
    jobs:
      - job: Review
        pool:
          vmImage: ubuntu-latest
        steps:
          - checkout: self
            fetchDepth: 0   # full history for diff

          - task: NodeTool@0
            inputs:
              versionSpec: "20.x"
            displayName: Set up Node.js

          - script: npm install -g @anthropic-ai/claude-code
            displayName: Install Claude Code

          - script: |
              git diff \
                "origin/$(System.PullRequest.TargetBranchName)...$(Build.SourceVersion)" \
                > /tmp/pr.diff
            displayName: Compute diff

          - script: |
              cat > /tmp/prompt.txt << 'PROMPT'
              Run the neohaskell-code-review skill on the diff below.
              Emit severity-ranked findings (blocker/major/minor/nit) with
              file:line citations and a concrete fix for each, then a one-line verdict.

              PROMPT
              cat /tmp/pr.diff >> /tmp/prompt.txt
              claude -p "$(cat /tmp/prompt.txt)" > /tmp/review.txt
            displayName: Run neohaskell-code-review
            env:
              ANTHROPIC_API_KEY: $(ANTHROPIC_API_KEY)

          - script: |
              BODY=$(cat /tmp/review.txt \
                | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))")
              ORG_URL="$(System.TeamFoundationCollectionUri)"
              PROJECT="$(System.TeamProject)"
              REPO="$(Build.Repository.Name)"
              PR_ID="$(System.PullRequest.PullRequestId)"
              curl --silent --fail-with-body \
                -X POST \
                -H "Authorization: Bearer $(System.AccessToken)" \
                -H "Content-Type: application/json" \
                -d "{\"comments\":[{\"content\":${BODY},\"commentType\":1}],\"status\":1}" \
                "${ORG_URL}${PROJECT}/_apis/git/repositories/${REPO}/pullRequests/${PR_ID}/threads?api-version=7.1"
            displayName: Post review comment

          - script: |
              if [ "$(FAIL_ON_BLOCKERS)" = "true" ] && grep -qi "blocker" /tmp/review.txt; then
                echo "##vso[task.logissue type=error]Blocker-severity findings detected."
                exit 1
              fi
            displayName: Fail on blockers
```

---

### Template D — Bitbucket Pipelines

File: add a step to `bitbucket-pipelines.yml`

Per-Provider Setup: create a **Repository Access Token** (or app password) with `pullrequest:write` scope. Add it as a repository variable named `BITBUCKET_TOKEN` (secured). Also add `ANTHROPIC_API_KEY` as a secured repository variable. Bitbucket provides `BITBUCKET_REPO_FULL_NAME` and `BITBUCKET_PR_ID` automatically.

```yaml
pipelines:
  pull-requests:
    '**':
      - step:
          name: NeoHaskell Code Review
          image: node:20-slim
          clone:
            depth: full   # full history for diff
          script:
            - apt-get update -qq && apt-get install -y -qq git curl python3
            - npm install -g @anthropic-ai/claude-code

            - export FAIL_ON_BLOCKERS="true"

            - git diff
                "origin/${BITBUCKET_PR_DESTINATION_BRANCH}...${BITBUCKET_COMMIT}"
                > /tmp/pr.diff

            - |
              cat > /tmp/prompt.txt << 'PROMPT'
              Run the neohaskell-code-review skill on the diff below.
              Emit severity-ranked findings (blocker/major/minor/nit) with
              file:line citations and a concrete fix for each, then a one-line verdict.

              PROMPT
              cat /tmp/pr.diff >> /tmp/prompt.txt
              claude -p "$(cat /tmp/prompt.txt)" > /tmp/review.txt

            - |
              BODY=$(cat /tmp/review.txt \
                | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))")
              curl --silent --fail-with-body \
                -X POST \
                -H "Authorization: Bearer ${BITBUCKET_TOKEN}" \
                -H "Content-Type: application/json" \
                -d "{\"content\":{\"raw\":${BODY}}}" \
                "https://api.bitbucket.org/2.0/repositories/${BITBUCKET_REPO_FULL_NAME}/pullrequests/${BITBUCKET_PR_ID}/comments"

            - |
              if [ "$FAIL_ON_BLOCKERS" = "true" ] && grep -qi "blocker" /tmp/review.txt; then
                echo "Blocker-severity findings detected. Failing the pipeline."
                exit 1
              fi
```

---

## DO / DON'T

| You might do — DON'T | NeoHaskell-correct — DO | Why |
|---|---|---|
| Emit a GitHub-only template regardless of the project's CI provider | Auto-detect the provider from the repo layout and emit only the matching template | The skill is provider-agnostic by design; forcing GitHub Actions on a GitLab project breaks immediately |
| Use `fetch-depth: 1` (shallow clone) | `fetch-depth: 0` (full history) or the provider equivalent | A shallow clone cannot compute a meaningful diff between base and head; `git diff` will fail or produce empty output |
| Hard-code `ANTHROPIC_API_KEY` in the YAML | Inject it from CI secrets / masked variables | A plaintext key in a committed file is a security blocker; every provider has a secrets store |
| Depend on CodeRabbit, SonarCloud, or another third-party review SaaS | Invoke `claude -p "..."` using the project's own `ANTHROPIC_API_KEY` | The whole point of this skill is a self-hosted, no-SaaS reviewer |
| Run `neo build` or `neo test` inside the review job | Only compute the diff and run `claude -p`; do not attempt to compile the project | The review is diff-scoped and static; building requires Nix and is a separate CI concern |
| Use `git diff HEAD~1...HEAD` as the diff | Use the actual base and head SHAs provided by the PR event | `HEAD~1` is one commit behind the merge commit, not the true base branch; it produces wrong diffs on multi-commit PRs |
| Post the review output as a commit status only | Post as a PR/MR **comment** (and optionally fail the check on blockers) | A comment is visible to reviewers immediately; a status check alone is easy to miss |
| Omit the `FAIL_ON_BLOCKERS` guard | Add a grep for `blocker` and exit 1 when `FAIL_ON_BLOCKERS=true` | Without a failing exit code the check always passes green, even on correctness regressions |
| Use `String` or `[Char]` in any Haskell you write | `Text` everywhere; `import Core` | Reminder: this pipeline reviews NeoHaskell; the reviewer knows the trap table — the CI just needs to call it |

---

## Large-diff note

`claude -p` runs a single prompt. If the PR diff is very large (thousands of lines), it may exceed the model's context window. In that case, split the diff by file and run one `claude -p` call per file, then concatenate the findings. Example:

```bash
git diff "$BASE"..."$HEAD" --name-only | while read -r file; do
  git diff "$BASE"..."$HEAD" -- "$file" > /tmp/file.diff
  claude -p "Run the neohaskell-code-review skill on this single-file diff:
$(cat /tmp/file.diff)" >> /tmp/review.txt
done
```

This is only needed for unusually large PRs; the standard single-call template handles typical feature-slice diffs comfortably.

---

## Verify

Trigger a test PR (even a trivial change) against the repository after adding the workflow file and the required secrets. Confirm:

1. The CI job appears in the PR's check list.
2. A review comment is posted by the CI bot on the PR.
3. If `FAIL_ON_BLOCKERS=true` and you plant a deliberate violation (e.g., add `import Data.Text` directly in a module), the check fails.
4. On a clean diff the check passes green.

There is no `neo build` step here — the review is static. The only external dependency is `ANTHROPIC_API_KEY` being valid and the `@anthropic-ai/claude-code` package being installable from npm.
