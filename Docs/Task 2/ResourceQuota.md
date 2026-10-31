# Task 2: ResourceQuota

The **memory-app-quota** limits total resources in the memory-app namespace.

| Resource | Three app Pods | Namespace quota |
| --- | --- | --- |
| Pods | 3 | 6 |
| CPU requests | 300m | 1 CPU |
| Memory requests | 384Mi | 1Gi |
| CPU limits | 1500m | 3 CPUs |
| Memory limits | 1200Mi | 3Gi |

Each Deployment allows one extra Pod during a rolling update. The quota permits
up to six app Pods, although terminating Pods can temporarily delay creation.
Debug Pods also count toward the quota.

The initContainers have lower resources than the app containers, so the table
does not need extra initContainer resources. Container restarts reuse the same
Pod and do not consume another Pod slot.

Quota does not reserve node capacity or prevent OOM kills. Scheduling still
depends on available node resources.

## Verify

~~~bash
kubectl -n memory-app describe resourcequota memory-app-quota
kubectl -n memory-app get deployments,pods
~~~

Compare Used with Hard. If creation exceeds quota, inspect ReplicaSet events for
FailedCreate or exceeded quota messages.
