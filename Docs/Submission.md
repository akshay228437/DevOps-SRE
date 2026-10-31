# Submission checklist

## Requirement coverage

| Area | Repository implementation | Final confirmation |
| --- | --- | --- |
| Container | Alpine, non-root, Docker HEALTHCHECK | Publish the rebuilt image containing the new health check |
| CI/CD | PR checks, three Python versions, GHCR and deployment PR | Latest required checks and release must pass in GitHub |
| Branch protection | Required-check names documented | Confirm main still requires PRs and prevents bypasses |
| GitOps | Argo CD Application with auto-sync, prune and self-heal | Application Synced after the final deployment PR |
| Kubernetes | Three Deployments, shared Service, 400Mi app limits | Inspect live manifests and OOM termination reasons |
| Supporting resources | ConfigMap, Secret references, initContainers, SA, RBAC, NetworkPolicy and quota | Create Secret before syncing; verify the three init logs |
| Metrics | Prometheus, Grafana, node and Pod dashboards | Previously confirmed; retain screenshots |
| Logs | Alloy and Loki | Previously confirmed; retain an application-log screenshot |
| Alerts | OOM and unready Pod rules saved in Grafana | Confirm Firing states/history; external delivery omitted by choice |

## Final cluster checks

Run on the EC2 control-plane node after the final changes are merged and synced:

~~~bash
kubectl -n argocd get application memory-app
kubectl -n memory-app get deployments,pods,svc
kubectl -n memory-app get endpointslices -l kubernetes.io/service-name=memory-app
kubectl -n memory-app get sa,role,rolebinding,networkpolicy,resourcequota,configmap
kubectl -n memory-app get secret memory-app-credentials
kubectl -n memory-app logs deployment/memory-app-py312 -c validate-runtime
kubectl -n memory-app logs deployment/memory-app-py313 -c validate-runtime
kubectl -n memory-app logs deployment/memory-app-py314 -c validate-runtime
kubectl -n memory-app get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{range .status.containerStatuses[*]}{.lastState.terminated.reason}{" "}{end}{"\n"}{end}'
kubectl -n monitoring get pods,pvc
~~~

Expected: Argo CD Synced, three Deployments, populated ready endpoints when the
app is serving, and successful Secret/configuration validation in each init log.
OOMKilled and restart backoff are expected for this deliberately leaking app.
Monitoring Pods should be Ready and PVCs Bound.

Use the individual Task 2 guides for RBAC and NetworkPolicy verification. Do not
claim enforcement is verified from the existence of resource objects alone.

## Evidence to retain

- GitHub main protection settings, successful PR checks and image release.
- Deployment PR with all three image tags, plus Argo CD Synced status.
- Container OOM reason and Secret validation logs, without Secret values.
- Grafana node metrics, Pod metrics, application logs and alert history.

## Limitations to disclose

- AWS EC2 differs from the brief's local-cluster requirement. Obtain evaluator
  acceptance or demonstrate the same setup locally before submission.
- Temporary vulnerability exceptions remain in .trivyignore.
- Secret injection is a demonstration; the application does not authenticate
  with APP_TOKEN.
- Local volumes are tied to their nodes; the setup is not highly available.
- Alert rules are created through the Grafana UI and must be recreated if its
  database is lost. Instructions are in [Task 3](Task%203/Alerts.md).

Do not mark the submission ready until the final Secret deployment, image
release, GitOps sync and alert evidence have been confirmed.
