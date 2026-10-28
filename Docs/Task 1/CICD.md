# Task 1.2: Secure CI/CD Pipeline

## Delivery flow

```text
Application PR -> required checks -> merge into main
  -> build, scan, and publish three Python images
  -> bot commits image tags on a new branch and opens a deployment PR
  -> approve workflow runs if GitHub requests it -> required checks -> review and merge
  -> Argo CD sync (manual initially; automatic sync remains to be enabled)
```

## Pull request checks

Workflow: [pr-checks.yml](../../.github/workflows/pr-checks.yml)

Every PR targeting `main` runs the checks, including manifest-only PRs.
There is no PR path filter, so required checks are not left waiting by path exclusions.

- Flake8 runs once.
- CodeQL runs once and uploads security findings.
- pytest runs on Python 3.12, 3.13, and 3.14.
- Docker builds and Trivy scans each Python Alpine image.
- No application container smoke test is performed.

Trivy fails on HIGH/CRITICAL findings except the explicit temporary exceptions in
`.trivyignore`. Those exceptions suppress findings; they do not remediate them.
CodeQL job success alone does not enforce zero findings; configure code scanning
merge protection separately.

## Protecting main

Require PRs and prevent bypasses. Require these status checks:

- `Lint`
- `CodeQL`
- `Unit Tests (Python 3.12)`
- `Unit Tests (Python 3.13)`
- `Unit Tests (Python 3.14)`
- `Build and Scan Image (Python 3.12)`
- `Build and Scan Image (Python 3.13)`
- `Build and Scan Image (Python 3.14)`

Retain the CodeQL code-scanning results requirement as well. GitHub settings are
external to this repository and must be verified there. Release jobs are not
pre-merge requirements.

## Release pipeline

Workflow: [release.yml](../../.github/workflows/release.yml)

The workflow handles closed PRs targeting `main`; the release job runs only for
merged PRs. It skips PRs whose changed files are all under `k8s/`, `argocd/`,
`Docs/`, or match `**/*.md`. A mixed PR with other changed files still releases.

The matrix checks out the merged commit and builds Python 3.12, 3.13, and 3.14
images. Each image is scanned again before publishing because the build pulls
fresh base images. Public GHCR images use tags such as:

```text
ghcr.io/akshay228437/devops-sre:py3.12-sha-<merged-commit-sha>
```

Only after every matrix job succeeds does `update-manifests` run. It checks out
`main` and uses `scripts/update-image-tags.py` to update the image reference and
version label in each of the three Deployment manifests. The script validates
all three files before writing and rejects malformed commit SHAs.

`peter-evans/create-pull-request` commits only `k8s/deployment-*.yaml` to
`automation/update-images-<merged-commit-sha>` and creates a PR targeting `main`.
Rerunning a release reuses its branch; unchanged tags produce no new commit.
Different releases have separate PRs: review their source commits and avoid
merging an older deployment PR after a newer one unless rolling back deliberately.

The bot does not merge the PR or bypass protection. The deployment PR changes
only `k8s/`, so merging it does not publish images or create another update PR.
PR checks still run independently.

## GitHub setup and authentication

Publishing uses the built-in `GITHUB_TOKEN` with `packages: write`.
The manifest-update job uses that token with `contents: write` and
`pull-requests: write`; no PAT is configured.

In Settings -> Actions -> General -> Workflow permissions, enable:
**Allow GitHub Actions to create and approve pull requests**.
This permits PR creation; the workflow does not approve or merge its own PR.
Organization policy may control this setting.

GitHub may require a user with write access to select **Approve workflows to run**
on PRs created with `GITHUB_TOKEN`. If the bot PR's checks have not started,
inspect its banner before waiting for required checks. See the current
[GitHub token documentation](https://docs.github.com/en/actions/concepts/security/github_token).

## Verification status

The updater was exercised against copies of the current manifest content in
memory: three image/label changes, idempotence, invalid input rejection, and
failure before writing when a manifest is malformed. End-to-end bot PR creation,
GitHub permissions, required checks, and AWS deployment need validation in GitHub
and the cluster after merging these workflow changes.
