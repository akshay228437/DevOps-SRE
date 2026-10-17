# Task 1.2: Secure CI/CD Pipeline

## Overview

We use GitHub Actions to check pull requests and publish the application image after merging into `main`.

```text
Working branch -> Pull request -> CI checks -> Merge into main -> Build and publish to GHCR
```

## Pull Request Checks

Workflow: [pr-checks.yml](../../.github/workflows/pr-checks.yml)

Runs when a pull request targets `main`, including when new commits are pushed to that pull request.

Four jobs run independently:

| Job | Tool | Purpose |
| --- | --- | --- |
| Lint | Flake8 | Check Python formatting and basic coding mistakes |
| Unit Tests | pytest | Run the tests in `test/` |
| CodeQL | GitHub CodeQL | Scan Python code for security vulnerabilities |
| Build and Scan Image | Docker and Trivy | Build the image and scan it for HIGH and CRITICAL vulnerabilities |

The pipeline does not start the application container. Trivy returns a failure when it detects HIGH or CRITICAL vulnerabilities. CodeQL uploads findings to GitHub; merge protection must enforce the findings policy separately.

## Protecting main

The GitHub protection settings used for this setup are:

- Require a pull request before merging into `main`.
- Require `Lint`, `Unit Tests`, `CodeQL`, and `Build and Scan Image` to pass.
- Prevent bypassing the protection rules.
- Use a ruleset targeting `main` with **Require code scanning results**, selecting CodeQL and the desired alert thresholds.

These settings are managed in GitHub, not in the workflow files. Their enforcement must be verified in the repository settings.

## Release Pipeline

Workflow: [release.yml](../../.github/workflows/release.yml)

The workflow listens for closed pull requests targeting `main`. Its release job runs only when the pull request was merged; closing without merging skips the job.

One job performs the following steps:

1. Checks out the merged commit.
2. Builds the Docker image.
3. Logs in to GitHub Container Registry (GHCR).
4. Pushes the image with a commit-based tag.
5. Displays the published image reference in the workflow summary.

Example image reference:

```text
ghcr.io/akshay228437/devops-sre:sha-<merged-commit-sha>
```

The release job contains no Trivy scan. Security scanning happens in the PR workflow.

## Authentication

Publishing uses GitHub's automatic `GITHUB_TOKEN` with `packages: write` permission. No manually created token or Docker Hub credentials are needed.

## Issues Resolved

- Fixed trailing spaces, blank-line spacing, and long lines reported by Flake8.
- Changed the Docker base image from Debian-based Python slim to Python Alpine after Trivy reported HIGH vulnerabilities in Debian packages.
- The PR workflow was reported as successful after the fixes.

