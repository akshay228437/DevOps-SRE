# Task 2: Initial application NetworkPolicy

`k8s/networkpolicy.yaml` applies to Pods labelled
`app.kubernetes.io/name: memory-app` in the `memory-app` namespace.
It permits incoming TCP 8080 from Pods in the same namespace. Other incoming
Pod traffic is denied unless another policy adds an allowance. Policies are
additive: this file cannot override an allowance in another applicable policy.

Only Ingress is selected, so this policy does not restrict outgoing traffic.
The application Service remains ClusterIP on port 80, targeting Pod port 8080.
The policy uses the Pod destination port, not the Service port.

Calico must be healthy and enforcing Kubernetes NetworkPolicies. Standard
NetworkPolicy has node-traffic exceptions; this is not a firewall against every
host-originated connection. Kubelet probes are not deliberately blocked by this
policy. Argo CD's NodePort Service is in another namespace and is unchanged.
Port-forward uses the API/kubelet path and is not an appropriate test of Pod
network isolation.

This initial policy trusts all client Pods in `memory-app`; namespace write
access therefore remains a trust boundary. Tighten client labels if needed.
Before Task 3 introduces health-check monitoring from a separate namespace,
add an explicit allowance for the selected monitoring Pods on TCP 8080.
Node-based log collection and cluster metrics have separate network paths.

## Deployment and verification

Merge the policy through a PR and allow Argo CD to sync. On the control-plane
node, inspect its interpretation:

```bash
kubectl -n memory-app get networkpolicy
kubectl -n memory-app describe networkpolicy allow-namespace-http
```

Test an allowed request from an existing application Pod (no extra Pod or quota
usage is needed). This runs a short HTTP client, not another leaking process:

```bash
kubectl -n memory-app exec deployment/memory-app-py312 -- python -c 'import urllib.request; print(urllib.request.urlopen("http://memory-app/healthcheck", timeout=5).read().decode())'
```

Expect the healthy JSON response. Run while the client and Service backends are
ready; OOM restarts can independently interrupt connections.

For a blocked request from another namespace, obtain the existing application's
image and start a short-lived client in `default`:

```bash
IMAGE=$(kubectl -n memory-app get deployment memory-app-py312 -o jsonpath='{.spec.template.spec.containers[0].image}')
kubectl -n default run memory-app-netcheck --image="$IMAGE" --restart=Never --attach --rm --overrides='{"spec":{"automountServiceAccountToken":false}}' --command -- python -c 'import urllib.request; print(urllib.request.urlopen("http://memory-app.memory-app.svc.cluster.local/healthcheck", timeout=5).read().decode())'
```

Expect a connection timeout, not a healthy response. DNS resolution errors,
image pull errors, Pod admission failures, or an unavailable application do not
prove policy enforcement. Check the allowed request first. The client uses
ordinary Pod networking, not host networking. If interrupted before cleanup,
remove only the test Pod with `kubectl -n default delete pod memory-app-netcheck`.
Other policies or quotas in `default` may need to be accounted for in your cluster.

These are verification instructions, not results. Local manifest rendering
does not establish network enforcement; verify on the AWS cluster after sync.
