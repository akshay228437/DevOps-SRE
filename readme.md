# DevOps and SRE Project

A Python service with intentional memory growth, used to demonstrate containerization, secure CI/CD, GitOps deployment, and observability.

The current setup uses a non-root Python Alpine container and GitHub Actions for linting, unit tests, CodeQL analysis, container vulnerability scanning, and publishing images to GHCR after a pull request merges into `main`.

## Task 1

- [Task 1.1 Dockerization](Docs/Task%201/Dockerize.md)
- [Task 1.2 Secure CI/CD Pipeline](Docs/Task%201/CICD.md)
