# Task 2: Support RBAC

The **memory-app-support** Role allows reading Pods, logs, Services, events,
Deployments, ReplicaSets and EndpointSlices in memory-app.

Its RoleBinding grants access to the **memory-app-support** group.
It does not grant Secret access, resource changes, exec or port forwarding.
It is separate from the application's ServiceAccount.

A RoleBinding does not create users or group membership. Real support logins
require the cluster's authentication system to supply this group.

## Verify

Run with administrator impersonation permissions:

~~~bash
# Expected: yes
kubectl auth can-i list pods -n memory-app --as=support-check --as-group=memory-app-support
kubectl auth can-i get pods --subresource=log -n memory-app --as=support-check --as-group=memory-app-support

# Expected: no
kubectl auth can-i get secrets -n memory-app --as=support-check --as-group=memory-app-support
kubectl auth can-i delete pods -n memory-app --as=support-check --as-group=memory-app-support
kubectl auth can-i list pods -n kube-system --as=support-check --as-group=memory-app-support
~~~

These commands check authorization; they do not log in a real support user.
Other bindings can grant additional permissions.
