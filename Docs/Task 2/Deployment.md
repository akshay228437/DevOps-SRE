# Task 2: Kubernetes and GitOps

## Resources

The k8s/ directory is managed by Argo CD and contains:

- Namespace: memory-app.
- Three Deployments: memory-app-py312, memory-app-py313 and memory-app-py314.
- One ClusterIP Service: port 80 forwards to container port 8080.
- ConfigMap, initContainers, ServiceAccount, support RBAC, NetworkPolicy and ResourceQuota.
- References to a Secret created separately on the cluster.

Each Deployment has one replica using a public GHCR image. No image-pull Secret
is required. Each application container requests 100m CPU and 128Mi memory,
with limits of 500m CPU and 400Mi memory.

The app intentionally consumes memory until it is OOMKilled. Kubernetes restarts
it; repeated failures can cause CrashLoopBackOff. This is expected behavior.

Startup, readiness and liveness probes call /healthcheck. The Service routes
to ready Pods. Each version has one replica, so its restarts can interrupt access
to that version.

Containers run as UID/GID 10001, without privilege escalation, with dropped
capabilities, a read-only root filesystem and RuntimeDefault seccomp.

## Argo CD

[application.yaml](../../argocd/application.yaml) tracks this repository's main
branch and k8s/ directory. Automatic sync deploys Git changes, self-heal corrects
live drift, and prune removes tracked resources deleted from Git.

[project.yaml](../../argocd/project.yaml) limits the repository, destination and
resource kinds Argo CD may manage. It does not limit manual kubectl access.
Namespace is a cluster-scoped kind exception; its name is not restricted by that
whitelist. Untracked resources are not automatically pruned.

## Prerequisites and Argo CD installation

Start with a working Kubernetes cluster, kubectl administrator access and a
NetworkPolicy-capable network plugin. The demonstrated environment uses
Kubernetes 1.34.5 and Calico on three EC2 nodes. Cluster/node provisioning is
not automated by this repository.

For a fresh cluster, install the standard Argo CD version used for this setup:

~~~bash
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
kubectl apply --server-side -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/v3.5.6/manifests/install.yaml
kubectl -n argocd rollout status deployment/argocd-server --timeout=300s
kubectl -n argocd get pods
~~~

For temporary access from the same machine, run:

~~~bash
kubectl -n argocd port-forward svc/argocd-server 8443:443
~~~

Open https://127.0.0.1:8443. The standard installation uses a self-signed
certificate. Username: admin. In another terminal, retrieve the initial password:

~~~bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 --decode; echo
~~~

Change the initial password after login. On a remote EC2 node, port forwarding
binds that node's loopback address; use an SSH tunnel to access it from your
computer. The existing deployment has separately configured NodePort access.

Source: [Argo CD installation guide](https://argo-cd.readthedocs.io/en/stable/getting_started/).

## Deploy

Create the [Secret](Secret.md) before merging Deployment references.
Merge manifests through a PR. From the updated repository on the control-plane
node, bootstrap the project and Application if not already installed:

~~~bash
kubectl apply -f argocd/project.yaml
kubectl apply -f argocd/application.yaml
~~~

Argo CD manages the application resources; do not apply the Deployments manually.
The Application and AppProject are outside k8s/, so changes to those bootstrap
files must be applied separately.

## Verify

~~~bash
kubectl -n argocd get application memory-app
kubectl -n memory-app get deployments,pods,svc
kubectl -n memory-app get endpointslices -l kubernetes.io/service-name=memory-app
kubectl -n memory-app logs deployment/memory-app-py312 -c validate-runtime
~~~

Expect Synced in Argo CD. Health can change as the intentional OOM failures
cause restarts. The init log should say **Runtime configuration and Secret validated**
after the Secret changes are deployed.

For temporary local access, run:

~~~bash
kubectl -n memory-app port-forward svc/memory-app 8081:80
~~~

From the same machine, open http://127.0.0.1:8081/healthcheck.
Port forwarding reaches a selected Pod; it does not test Service load balancing
or NetworkPolicy enforcement.

