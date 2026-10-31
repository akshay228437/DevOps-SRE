# Task 3: Grafana Alerts

See the [Task 3 overview](README.md) for installation and evaluation checks.

Two Grafana-managed rules were created manually under **Alerting -> Alert rules**.
They query Prometheus and are stored in Grafana's persistent database.
They are not provisioned by the Helm values file; recreate them using this guide
if the Grafana database is lost.

Create a folder named **Memory App** and an evaluation group named
**memory-app** with a **1m** evaluation interval.

## OOM kill

Name: **Memory App OOMKilled**.

Select Prometheus, use the Code editor and set the query type to Instant:

~~~promql
(
  kube_pod_container_status_last_terminated_reason{
    namespace="memory-app",
    container="memory-app",
    reason="OOMKilled"
  } == 1
)
and on(namespace, pod, container)
(
  increase(kube_pod_container_status_restarts_total{
    namespace="memory-app",
    container="memory-app"
  }[5m]) > 0
)
~~~

Set the threshold to **Above 0**, pending period to **None**, keep firing for
to **None**, no-data state to **Normal**, and error state to **Alerting**.

Summary: Memory app container restarted after an OOM kill.

This matches a recent restart where the latest recorded termination was
OOMKilled. It is based on sampled metrics, not an exact event log.
An OOM kill does not need to appear in application logs.

## Unready Pod

Name: **Memory App Pod Unready**. Use an Instant Prometheus query:

~~~promql
kube_pod_status_ready{
  namespace="memory-app",
  condition="true"
}
~~~

Set the threshold to **Below 1**, pending period to **2m**, keep firing for
to **None**, no-data state to **Normal**, and error state to **Alerting**.

Summary: Memory app Pod has remained unready for two minutes.

The pending period avoids alerts for short startup or restart delays. This rule
checks existing Pods; it does not detect a Deployment with no Pods or directly
probe the HTTP endpoint.

## Verify

Open the folder in Alert rules and inspect each rule's instances/history.
The intentionally leaking application provides OOM failures naturally.
Expect the OOM rule to fire after a matching recent restart. The unready rule
fires only if a Pod stays unready continuously for two minutes.

Both rules were saved. Confirm Firing states before recording alert execution
as verified. Alerts are displayed in Grafana; Slack and email delivery were
left out by choice.
