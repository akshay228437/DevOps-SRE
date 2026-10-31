# Task 3: Monitoring

Install kube-prometheus-stack with Helm in the `monitoring` namespace.
This directory is outside the application directory tracked by Argo CD.
Run the commands below from the repository root on the control-plane node
after transferring or merging these files.

## Install

The cluster must already have the `local-path` StorageClass.

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --version 92.16.1 \
  --namespace monitoring --create-namespace \
  --values monitoring/prometheus-values.yaml \
  --wait --timeout 10m
```

## Verify

```bash
helm status monitoring -n monitoring
kubectl -n monitoring get pods
kubectl -n monitoring get pvc
kubectl -n monitoring get svc monitoring-grafana
```

PVCs should become Bound once their consuming Pods are scheduled. Prometheus
and Alertmanager Pods are created by the operator after Helm creates their
custom resources; check that these Pods also reach Running and Ready.

Grafana is available at `http://<EC2-public-IP>:30300`. Allow inbound TCP 30300
from your own public IP in the node security group. Username: `admin`.
Retrieve the chart-generated password on the cluster; do not commit it:

```bash
kubectl -n monitoring get secret monitoring-grafana \
  -o jsonpath='{.data.admin-password}' | base64 --decode; echo
```

Grafana includes a Prometheus data source and Kubernetes dashboards. Check node
CPU, memory and filesystem dashboards, then Pod CPU, memory and restart metrics.

For Prometheus target inspection, run this in a separate terminal:

```bash
kubectl -n monitoring port-forward svc/monitoring-kube-prometheus-prometheus 9090:9090
```

Open `http://127.0.0.1:9090/targets` from that machine (or tunnel it to your
computer). Review unreachable targets before considering installation complete;
self-managed control-plane metrics may require separate endpoint configuration.

## Capacity and persistence

One replica each of Prometheus, Grafana and Alertmanager requests 5Gi, 1Gi and
1Gi of local storage. Prometheus retains at most two days of metrics and removes
old blocks at a 3GB retention threshold, leaving space for its write-ahead log
and active data. The retention threshold is not a total disk-usage cap.

Local Path Provisioner does not enforce the requested PVC capacity as a disk
quota. All local volumes share the hosting node's disk with its other workloads.
Monitor free space, especially when logging is added. Data survives Pod
replacement on its original node; node loss makes that data unavailable.
The StorageClass uses Delete reclaim policy, so deleting a PVC can remove data.

Resource settings are initial values for this small assignment cluster. Review
actual usage after installation; sidecars and installation jobs add overhead.

## Remaining work

- Verify dashboards and scrape targets on the cluster.
- Install centralized logging and connect it to Grafana.
- Configure Grafana alerts for unhealthy Pods and OOM kills.
- Add health endpoint probing and the corresponding application NetworkPolicy
  allowance when setting up health monitoring. The app has no metrics endpoint.

## Centralized application logs: Loki and Alloy

The flow is application stdout/stderr -> Kubernetes logs API -> Alloy -> Loki
-> Grafana. One Alloy Deployment collects only `memory-app` Pod logs using
namespace-scoped read permissions. No node filesystem mounts or changes to the
application NetworkPolicy are required for API-based collection. The application
source code stays unchanged. This does not collect host system logs.

Loki runs as one monolithic instance with a 3Gi `local-path` PVC, a 512Mi memory
request and a 1Gi limit. Log retention is 48 hours with asynchronous deletion;
this is not a disk quota. Caches and rule sidecars are disabled for this small
setup. Loki is accessible through an internal ClusterIP gateway without tenant
authentication; do not expose the gateway using NodePort or a public ingress.
Local storage has the same node-loss and disk-space limitations described above.

Run from the repository root on the control-plane node after copying these files:

```bash
helm repo add grafana-community https://grafana-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

helm upgrade --install loki grafana-community/loki \
  --version 20.2.0 --namespace monitoring \
  --values monitoring/loki-values.yaml \
  --wait --timeout 10m

helm upgrade --install alloy grafana/alloy \
  --version 1.15.0 --namespace monitoring \
  --values monitoring/alloy-values.yaml \
  --wait --timeout 10m

# Provision the Loki data source in the existing Grafana installation.
helm upgrade monitoring prometheus-community/kube-prometheus-stack \
  --version 92.16.1 --namespace monitoring \
  --values monitoring/prometheus-values.yaml \
  --wait --timeout 10m
```

Verify the releases and log collector:

```bash
kubectl -n monitoring get pods,pvc
kubectl -n monitoring logs deployment/alloy -c alloy --tail=50
```

In Grafana, open Explore, select the Loki data source, select the Code editor,
and run this LogQL query with the time range set to the last 15 minutes:

```logql
{namespace="memory-app", container="memory-app"}
```

To include initContainer logs, use `{namespace="memory-app"}` instead. Verify
logs from all three Python versions using the Pod labels in the results.
Collection starts after Alloy is installed and is not an archival backfill.
Alloy has no persistent write buffer here: interrupted collection can lose logs,
and reconnecting streams can replay recent lines. OOM kills do not necessarily
produce an application log message; monitor Kubernetes OOM metrics separately.

Sources: [Loki Helm installation](https://grafana.com/docs/loki/latest/setup/install/helm/install-monolithic/)
and [Alloy Kubernetes log collection](https://grafana.com/docs/alloy/latest/reference/components/loki/loki.source.kubernetes/).
