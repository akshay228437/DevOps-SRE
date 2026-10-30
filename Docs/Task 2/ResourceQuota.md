# Task 2: Namespace ResourceQuota

`k8s/resourcequota.yaml` caps the aggregate resources admitted in the
`memory-app` namespace. It does not reserve node capacity or change individual
container limits. Each application container retains its 400Mi memory limit.

| Resource | Three application Pods | Six application Pods | Namespace quota |
| --- | --- | --- | --- |
| Pods | 3 | 6 | 6 |
| CPU requests | 300m | 600m | 1 CPU |
| Memory requests | 384Mi | 768Mi | 1Gi |
| CPU limits | 1500m | 3000m | 3 CPUs |
| Memory limits | 1200Mi | 2400Mi | 3Gi |

Each Deployment allows one surge Pod. Six Pods cover the desired three plus
three rollout surge Pods. Terminating Pods can still consume quota temporarily,
so additional creation may wait until those Pods finish. The six-Pod ceiling
also applies to debug Pods and Jobs in this namespace. The sequential BusyBox
initContainer requests 25m CPU/32Mi and is limited to 100m CPU/64Mi. Those values
are below the application resources, so effective Pod requests/limits and the
table above remain unchanged. Review future initContainers or sidecars separately.

The two workers each have 2 CPUs and approximately 3.64Gi allocatable memory.
Argo CD, networking, system workloads, and future monitoring share this capacity.
Quota acceptance does not guarantee enough free node resources for scheduling.
Check allocated requests with `kubectl describe nodes` before expanding usage.

With compute quotas enabled, new Pods must specify the corresponding CPU and
memory requests and limits; the current application containers already do.
Quota does not retroactively evict existing Pods. A rejected creation can appear
as `FailedCreate` with an `exceeded quota` message on its ReplicaSet.

## Deploy and verify

Merge through a PR and allow Argo CD to sync. Then run:

```bash
kubectl -n memory-app get resourcequota
kubectl -n memory-app describe resourcequota memory-app-quota
kubectl -n memory-app get deployments,pods
```

Compare the Used and Hard columns. Container restarts caused by the intentional
memory leak do not themselves create new Pods and do not add Pod quota usage.

The manifest has not been applied to AWS by these local file changes. Cluster
quota usage and rollout behavior still require verification after sync.
