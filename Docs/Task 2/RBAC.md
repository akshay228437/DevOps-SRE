# Task 2: Read-only support group

`k8s/rbac.yaml` defines a Role and RoleBinding in `memory-app`:

- The Role permits get/list/watch on Pods, Services, events, Deployments,
  ReplicaSets, and EndpointSlices, plus get on Pod logs.
- The RoleBinding grants these permissions to the group `memory-app-support`.
- It grants no Secret access, changes, exec, or port forwarding.
- It does not bind to the application ServiceAccount. Only one custom
  ServiceAccount remains, with token mounting disabled.

The group name is the intended support identity. Creating a RoleBinding does not
create people, passwords, group membership, or an authentication integration.
Until the cluster authenticator supplies this group for real users, the binding
has no real support-user login attached. Do not describe that integration as done.

Namespace-scoped logs may contain sensitive data; read-only does not imply that
all readable content is public. Existing administrator permissions remain broader
and are not reduced by this binding.

## Verify authorization after GitOps sync

Using administrator credentials with user/group impersonation permissions:

```bash
kubectl -n memory-app get role,rolebinding

# Expected yes
kubectl auth can-i list pods -n memory-app --as=support-check --as-group=memory-app-support
kubectl auth can-i get pods --subresource=log -n memory-app --as=support-check --as-group=memory-app-support

# Expected no
kubectl auth can-i get secrets -n memory-app --as=support-check --as-group=memory-app-support
kubectl auth can-i delete pods -n memory-app --as=support-check --as-group=memory-app-support
kubectl auth can-i list pods -n kube-system --as=support-check --as-group=memory-app-support
kubectl auth can-i list pods -n memory-app --as=system:serviceaccount:memory-app:memory-app
```

These checks test the authorization rules. They do not create or log in a user.
Investigate any unexpected permissions from other bindings.
