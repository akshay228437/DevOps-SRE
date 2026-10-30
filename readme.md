# DevOps and SRE Project

A Python service with intentional memory growth, used to demonstrate containerization, secure CI/CD, GitOps deployment, and observability.

The current setup uses a non-root Python Alpine container and GitHub Actions for linting, unit tests, CodeQL analysis, container vulnerability scanning, and publishing images to GHCR after a pull request merges into `main`.

## Task 1

- [Task 1.1 Dockerization](Docs/Task%201/Dockerize.md)
- [Task 1.2 Secure CI/CD Pipeline](Docs/Task%201/CICD.md)

## Task 2

- [Deployment and GitOps setup](Docs/Task%202/Deployment.md)
- [Application ServiceAccount](Docs/Task%202/ServiceAccount.md)
- [Support RBAC](Docs/Task%202/RBAC.md)
- [Runtime ConfigMap and initContainers](Docs/Task%202/Configuration.md)
- [NetworkPolicy](Docs/Task%202/NetworkPolicy.md)
- [ResourceQuota](Docs/Task%202/ResourceQuota.md)

Runtime configuration and a BusyBox initContainer keep application code unchanged.
Secret integration is deferred until after Task 3. Cluster-side
verification is required after the changes are merged and synced.
