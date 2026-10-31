# Task 2: NetworkPolicy

The **allow-namespace-http** policy selects application Pods in memory-app.

- Allows incoming TCP 8080 from Pods in the same namespace.
- Blocks other incoming Pod traffic unless another applicable policy allows it.
- Does not restrict outgoing traffic.

The Service exposes port 80, but the policy uses the destination container port,
8080. Calico enforces the policy. Kubernetes has node-traffic exceptions;
port forwarding is not a test of Pod isolation.

Prometheus collects Pod metrics through Kubernetes components. Alloy collects
logs through the Kubernetes API. Neither requires direct access to the app's
HTTP endpoint. A future HTTP probe from monitoring would need an explicit
NetworkPolicy allowance.

## Verify

~~~bash
kubectl -n memory-app describe networkpolicy allow-namespace-http

# Allowed: request from an application Pod.
kubectl -n memory-app exec deployment/memory-app-py312 -c memory-app -- python -c 'import urllib.request; print(urllib.request.urlopen("http://memory-app/healthcheck", timeout=5).read().decode())'
~~~

Expect the healthy JSON response. Run while the application is ready because
its deliberate OOM restarts can also interrupt requests.

Test a blocked request from a temporary Pod in default:

~~~bash
IMAGE=$(kubectl -n memory-app get deployment memory-app-py312 -o jsonpath='{.spec.template.spec.containers[0].image}')
kubectl -n default run memory-app-netcheck --image="$IMAGE" --restart=Never --attach --rm --overrides='{"spec":{"automountServiceAccountToken":false}}' --command -- python -c 'import urllib.request; print(urllib.request.urlopen("http://memory-app.memory-app.svc.cluster.local/healthcheck", timeout=5).read().decode())'
~~~

Expect a timeout. Confirm the allowed request works first: DNS failures, image
pull failures and an unavailable backend do not prove policy enforcement.
