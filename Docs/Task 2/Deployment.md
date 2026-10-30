# Task 2: Initial Kubernetes deployment

## Scope

The flat `k8s/` directory contains a Namespace, three Deployments, one shared
ClusterIP Service, a ServiceAccount, runtime ConfigMap, BusyBox initContainers,
support RBAC, NetworkPolicy,
and ResourceQuota. Argo CD tracks this directory on `main`.

Each Deployment runs one replica of the same application commit with Python
3.12, 3.13, or 3.14. Images are public GHCR packages and need no image-pull secret.
Commit-based tags identify the release; registry tags can still be overwritten.
Digest pinning is a future hardening step.

## Resources and availability

Each application container requests 100m CPU and 128Mi memory and is limited
to 500m CPU and 400Mi memory. Three Pods request 300m CPU and 384Mi memory in
total; their combined memory limits are 1200Mi. Rolling updates can temporarily
create additional Pods. Capacity must also cover Kubernetes and Argo CD.

The memory leak remains intentional. The kernel enforces the container memory
limit and can kill the process; the kubelet restarts the container in the same
Pod. Repeated failures can produce restart backoff. The scheduler places Pods
using requests; it does not perform OOM kills. The 128Mi request covers startup,
not the application's growing steady-state consumption.

Startup, readiness, and liveness probes call `/healthcheck`. This endpoint does
not predict memory exhaustion. The Service sends connections to ready endpoints;
an exact traffic split is not guaranteed. One replica per version cannot ensure
continuous availability for that version during OOM restarts.

A soft topology spread constraint encourages placement across workers without
blocking scheduling. The existing control-plane taint is expected to keep these
workloads off that node.

## Container security

Containers use UID/GID 10001, a read-only root filesystem, RuntimeDefault seccomp,
no privilege escalation, and no Linux capabilities. Service account tokens are
not mounted. These are workload settings; no admission enforcement is added.

## Review and deployment

Commit these files through a PR. Before syncing with Argo CD, validate against
the AWS cluster from a checkout of the merged repository:

```bash
kubectl apply --dry-run=server -f k8s/namespace.yaml
```

Other resources require the namespace to exist for server validation.

The Argo CD Application is defined in `argocd/application.yaml`, outside the
tracked `k8s/` directory. It uses the dedicated `memory-app` AppProject with
automatic sync, pruning, and self-healing enabled. Bootstrap the project before
switching the Application to it. The project permits only this repository,
the in-cluster destination namespace, and listed resource kinds.

The Namespace kind is a deliberate cluster-scoped exception because `k8s/`
contains the Namespace manifest. This whitelist restricts kind, not Namespace
object name; protect repository writes and review namespace changes. The
AppProject does not reduce the underlying Argo CD controller's cluster RBAC.
Secrets are not allowed by the project yet and will be addressed in the final step.

After merging the manifests into `main`, run these commands from the repository
root on the control-plane node, using a checkout containing the merged files:

```bash
kubectl apply --dry-run=server -f argocd/project.yaml
kubectl apply -f argocd/project.yaml
kubectl apply --dry-run=server -f argocd/application.yaml
kubectl apply -f argocd/application.yaml
kubectl -n argocd get application memory-app
```

In the Argo CD UI, open `memory-app` and review its resources and sync status.
The Application enables namespace creation. Do not manually apply the
Deployments; Argo CD manages deployment automatically. Pruning deletes tracked
resources removed from Git, and self-healing corrects live drift from Git.
Because the Application manifest is outside the tracked `k8s/` directory, apply
changes to `argocd/application.yaml` explicitly; this Application does not manage itself.

After syncing:

```bash
kubectl -n memory-app get deployments,pods,svc -o wide
kubectl -n memory-app get endpointslices -l kubernetes.io/service-name=memory-app
kubectl -n memory-app get pods -w
kubectl -n memory-app get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{range .status.containerStatuses[*]}{.restartCount}{"\t"}{.lastState.terminated.reason}{end}{"\n"}{end}'
```

For a temporary health check, run the port forward in a separate terminal:

```bash
kubectl -n memory-app port-forward svc/memory-app 8081:80
```

Then call `curl http://127.0.0.1:8081/healthcheck`. Port forwarding reaches a
selected Pod and does not validate Service load distribution across all Pods.

## Remaining task requirements

Secret design and implementation are deliberately deferred until after Task 3.
The runtime ConfigMap and BusyBox initContainers are configured without changing
application source code or adding test files.
Support RBAC and the dedicated AppProject are configured locally; validate their
behavior after GitOps sync.
Automatic image-tag update PRs are
configured in the release workflow; GitHub permissions and end-to-end operation
must be verified after merging the workflow changes.
This initial deployment does not complete Task 2.

