# DevOps and SRE Project

A Python service that deliberately grows its memory usage to demonstrate Docker,
CI/CD, Kubernetes, GitOps, monitoring, logging and alerts.

## Task 1: Docker and CI/CD

- [Docker setup](Docs/Task%201/Dockerize.md): non-root Python Alpine image and health check.
- [CI/CD](Docs/Task%201/CICD.md): PR checks, three Python versions, GHCR publishing and image-update PRs.

## Task 2: Kubernetes and Argo CD

Three Deployments run Python 3.12, 3.13 and 3.14 behind one ClusterIP Service.
Each application container has a 400Mi memory limit. OOM kills and restart
backoff are expected because the memory leak is intentional.

- [Deployment and GitOps](Docs/Task%202/Deployment.md)
- [ServiceAccount](Docs/Task%202/ServiceAccount.md)
- [Support RBAC](Docs/Task%202/RBAC.md)
- [ConfigMap and initContainer](Docs/Task%202/Configuration.md)
- [Secret](Docs/Task%202/Secret.md)
- [NetworkPolicy](Docs/Task%202/NetworkPolicy.md)
- [ResourceQuota](Docs/Task%202/ResourceQuota.md)

## Task 3: Observability

- [Task 3 setup and evaluation](Docs/Task%203/README.md)
- [Grafana alerts](Docs/Task%203/Alerts.md)

The cluster runs on three AWS EC2 nodes: one control-plane and two workers.
Monitoring uses local node storage.

## Architecture

~~~text
Application PR -> GitHub Actions -> GHCR images -> deployment PR
                                                   |
                                                   v
                                      main/k8s -> Argo CD -> 3 Deployments
                                                              |
                                                      shared ClusterIP Service

Nodes and Pod metrics -> Prometheus -> Grafana dashboards and alerts
Application logs -> Alloy -> Loki -> Grafana Explore
~~~
