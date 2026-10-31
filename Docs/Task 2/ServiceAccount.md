# Task 2: ServiceAccount

All three Deployments use the **memory-app** ServiceAccount.
Token mounting is disabled because the application does not call the Kubernetes
API. No RoleBinding grants this account application API permissions.

Kubernetes also creates a default ServiceAccount; the app does not use it.
The support RoleBinding applies to a separate group, not this ServiceAccount.

## Verify

~~~bash
kubectl -n memory-app get sa memory-app
kubectl -n memory-app get pods -o custom-columns='NAME:.metadata.name,SA:.spec.serviceAccountName,TOKEN-MOUNT:.spec.automountServiceAccountToken'
kubectl auth can-i get secrets -n memory-app --as=system:serviceaccount:memory-app:memory-app
~~~

Pods should show memory-app and false. The authorization check should return no,
unless other cluster bindings grant access. Impersonation checks require admin
permissions.

Secret injection is handled by the kubelet, so it does not require granting the
application ServiceAccount permission to read Secrets.
