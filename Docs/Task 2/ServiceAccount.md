# Task 2: Application ServiceAccount

All three application Deployments use the dedicated `memory-app` ServiceAccount
defined in `k8s/serviceaccounts.yaml`. Token mounting is disabled on both the
ServiceAccount and the Pod templates. The application does not call the Kubernetes
API, so no Role or RoleBinding is granted to this identity.

Only one custom ServiceAccount is configured. Kubernetes also creates a default
ServiceAccount in the namespace; that built-in account is not used by these Pods.
The separate demonstration reader account and its RBAC resources were removed
before deployment. A separate support Role now binds to the authenticated group
`memory-app-support`, not a second ServiceAccount. See `RBAC.md`.

Merge the manifest and Deployment changes through a PR. Argo CD syncs from main;
changing the Pod template's serviceAccountName triggers a rolling update.

After sync, verify on the control-plane node:

```bash
kubectl -n memory-app get serviceaccount memory-app
kubectl -n memory-app get pods -o custom-columns='NAME:.metadata.name,SA:.spec.serviceAccountName,TOKEN-MOUNT:.spec.automountServiceAccountToken'
```

Each application Pod should show `memory-app` and token mounting `false`.
Authorization can be checked with administrator impersonation permissions:

```bash
kubectl auth can-i list pods -n memory-app --as=system:serviceaccount:memory-app:memory-app
kubectl auth can-i get secrets -n memory-app --as=system:serviceaccount:memory-app:memory-app
```

Both should report `no` unless other cluster bindings grant access. These checks
still need to be run against the cluster after sync; no AWS changes were made
while editing the manifests.
