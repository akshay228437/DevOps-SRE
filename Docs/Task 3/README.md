# Task 3: Monitoring and Logging

Prometheus collects metrics, Grafana displays dashboards and alerts,
Alloy collects application logs, and Loki stores them.

## Evaluation overview

| Requirement | Implementation | Verification |
| --- | --- | --- |
| Node CPU, memory and disk | Prometheus and Node Exporter | Node Exporter / Nodes dashboard; three targets report up=1 |
| Pod CPU and memory | Prometheus Kubernetes metrics | Compute Resources / Pod dashboard, namespace memory-app |
| Centralized application logs | Alloy sends logs to Loki | Grafana Explore shows memory-app logs |
| OOM alert | Grafana-managed Prometheus rule | Rule saved; confirm Firing in alert history |
| Unready Pod alert | Grafana rule with a 2m pending period | Rule saved; confirm Firing during sustained unready state |
| Persistent storage | Local Path Provisioner | Prometheus, Grafana, Alertmanager and Loki PVCs |

Metrics and application logs were verified in Grafana. External Slack/email
notifications were left out by choice.

## Configuration files

- [Prometheus and Grafana values](../../monitoring/prometheus-values.yaml)
- [Loki values](../../monitoring/loki-values.yaml)
- [Alloy values](../../monitoring/alloy-values.yaml)
- [Grafana alert instructions](Alerts.md)

All components run in the **monitoring** namespace and are installed with Helm.
The Helm values are in monitoring/, outside the application's Argo CD path k8s/.
Run the commands below from the repository root on the EC2 control-plane node.

## 1. Local storage

The cluster uses Local Path Provisioner:

~~~bash
kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/v0.0.37/deploy/local-path-storage.yaml
kubectl -n local-path-storage rollout status deployment/local-path-provisioner --timeout=180s
kubectl get storageclass
~~~

Expect a StorageClass named local-path. WaitForFirstConsumer means a PVC can
stay Pending until its consuming Pod is scheduled.

## 2. Prometheus and Grafana

~~~bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --version 92.16.1 -n monitoring --create-namespace \
  -f monitoring/prometheus-values.yaml \
  --wait --timeout 10m
~~~

The chart also installs Alertmanager, kube-state-metrics, the Prometheus
Operator and a Node Exporter on each node.

~~~bash
kubectl -n monitoring get pods,pvc
~~~

All Pods should become Ready and PVCs Bound. The operator creates Prometheus
and Alertmanager Pods after their custom resources are installed.

Open **http://<EC2-public-IP>:30300**. Allow inbound TCP 30300 from your own
public IP in the node's EC2 security group.

Username: **admin**. Retrieve the generated password:

~~~bash
kubectl -n monitoring get secret monitoring-grafana \
  -o jsonpath='{.data.admin-password}' | base64 --decode; echo
~~~

Do not commit or share the password.

## 3. Verify metrics

In Grafana, open:

- **Node Exporter / Nodes** for node CPU, memory, disk and network.
- **Kubernetes / Compute Resources / Pod**, namespace memory-app, for app usage.

Set the time range to the last 15 minutes. In Explore, select Prometheus and run:

~~~promql
up{job="node-exporter"}
~~~

Expect three results, all equal to 1. A value of 0 means scraping fails.
This cluster needed inbound TCP **9100 between cluster node security groups**
to allow scraping all three node addresses. Keep that port restricted to
cluster nodes.

Other scrape targets, especially self-managed control-plane components, may
need separate configuration. Check Prometheus targets before claiming every
control-plane metric is collected.

Grafana initially hit its 256Mi limit and was OOMKilled. Its current request is
256Mi and limit is 512Mi; the replacement Pod was Ready with zero restarts at
verification.

## 4. Loki and Alloy

~~~bash
helm repo add grafana-community https://grafana-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

helm upgrade --install loki grafana-community/loki \
  --version 20.2.0 -n monitoring \
  -f monitoring/loki-values.yaml \
  --wait --timeout 10m

helm upgrade --install alloy grafana/alloy \
  --version 1.15.0 -n monitoring \
  -f monitoring/alloy-values.yaml \
  --wait --timeout 10m

# Provision Loki in the existing Grafana.
helm upgrade monitoring prometheus-community/kube-prometheus-stack \
  --version 92.16.1 -n monitoring \
  -f monitoring/prometheus-values.yaml \
  --wait --timeout 10m
~~~

Alloy runs as one Deployment. It reads Pod logs in memory-app through the
Kubernetes API using namespace-scoped RBAC. No node filesystem mounts or app
NetworkPolicy changes are needed. It does not collect node system logs.

Loki runs as one instance behind an internal gateway. Keep its unauthenticated
gateway inside the cluster.

~~~bash
kubectl -n monitoring get pods,pvc
kubectl -n monitoring logs deployment/alloy -c alloy --tail=50
~~~

In Grafana Explore, select Loki, switch to Code and run:

~~~logql
{namespace="memory-app", container="memory-app"}
~~~

Use the Pod labels to check logs from all three versions. Logs were verified
in Grafana. Collection is not a historical archive: interruptions can lose logs
and reconnecting streams can repeat recent lines.

## 5. Alerts

See [Grafana alert setup](Alerts.md) for OOM kills and unready Pods.
Both rules were saved through the UI. Firing-state verification is still needed.
External Slack/email notifications were not configured.

## Storage and limits

| Component | Local PVC | Retention |
| --- | --- | --- |
| Prometheus | 5Gi | 2 days, with a 3GB block-retention threshold |
| Grafana | 1Gi | Dashboards and settings |
| Alertmanager | 1Gi | Alertmanager state |
| Loki | 3Gi | 48 hours |

Local volumes share the node's disk. Requested PVC sizes are not enforced disk
quotas, and retention does not impose a hard total disk-usage limit.
Monitor free space with **df -h /** on both workers.

Data survives Pod replacement on its original node but is unavailable if that
node is lost. The StorageClass uses Delete reclaim policy: deleting a PVC can
remove its stored data. This is a small assignment setup with one replica per
stateful component, not a highly available storage design.
