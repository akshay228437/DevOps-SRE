# Task 1.2: CI/CD

## Delivery flow

Application PR -> checks -> merge into main -> build, scan and publish images
-> image-update PR -> review and merge -> Argo CD sync.

The workflows are in [.github/workflows](../../.github/workflows).

## PR checks

Every PR targeting main runs:

| Check | Purpose |
| --- | --- |
| Lint | Flake8 checks Python code style |
| CodeQL | Static security analysis |
| Unit Tests | pytest on Python 3.12, 3.13 and 3.14 |
| Build and Scan Image | Docker build and Trivy scan for each Python version |

Trivy fails on HIGH or CRITICAL findings except temporary exceptions listed in
.trivyignore. An exception hides a finding; it does not fix the vulnerability.
The workflow does not run the app container or scan the BusyBox init image.

Protect main by requiring PRs and these eight checks:

- Lint
- CodeQL
- Unit Tests (Python 3.12)
- Unit Tests (Python 3.13)
- Unit Tests (Python 3.14)
- Build and Scan Image (Python 3.12)
- Build and Scan Image (Python 3.13)
- Build and Scan Image (Python 3.14)

Keep the CodeQL code-scanning results requirement as well. A successful CodeQL
job means analysis completed; code-scanning merge protection controls findings.
Remove obsolete required check names if they remain pending.

## Release

The release workflow handles merged PRs targeting main. It builds and scans all
three images before publishing them to public GHCR packages. Tags identify the
Python version and merged commit:

~~~text
ghcr.io/akshay228437/devops-sre:py3.12-sha-<full-commit-sha>
~~~

After all versions succeed, scripts/update-image-tags.py updates the three
Deployment image references and version labels. BusyBox stays unchanged.

The bot commits only the Deployment manifests to **automation/update-images**
and opens or updates its PR. The branch is reused across releases; manifest
updates are serialized with a concurrency group. Review the source SHA before
merging because release builds can finish out of order.

PRs changing only k8s/, argocd/, Docs/ or Markdown files do not trigger a release.
This prevents deployment PR loops. PR checks still run. Changes to monitoring
YAML currently trigger a release because monitoring/ is not excluded.

## GitHub permissions

The built-in GITHUB_TOKEN publishes packages and creates deployment PRs.
Enable **Settings -> Actions -> General -> Workflow permissions ->
Allow GitHub Actions to create and approve pull requests**.

The workflow does not approve, merge or bypass protection. If GitHub requests
approval to run checks on a bot PR, a user with write access must approve the run.

## Verify

Check the Actions page for successful PR and release jobs, confirm the three
image tags in GHCR, and review the deployment PR. After merging it, check the
Argo CD application and Pod image references.
