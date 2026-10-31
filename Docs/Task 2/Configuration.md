# Task 2: ConfigMap and initContainer

The **memory-app-runtime** ConfigMap supplies:

| Setting | Value | Purpose |
| --- | --- | --- |
| PYTHONUNBUFFERED | 1 | Unbuffered Python stdout/stderr |
| PYTHONDONTWRITEBYTECODE | 1 | Prevent Python bytecode cache writes |

Python reads these settings directly. Application source code is unchanged.

Each Deployment has a **validate-runtime** initContainer using
busybox:1.37.0-musl. It checks both settings equal 1 and that the Secret-injected
APP_TOKEN is nonempty. It exits successfully before the application starts.
It does not print the token.

The initContainer runs as a non-root user with a read-only root filesystem.
Its request is 25m CPU/32Mi memory; its limit is 100m CPU/64Mi.
These are below the app resources, so they do not increase effective Pod requests.

## Verify

Create the [Secret](Secret.md) before deploying the references. After Argo CD sync:

~~~bash
kubectl -n memory-app get configmap memory-app-runtime
kubectl -n memory-app logs deployment/memory-app-py312 -c validate-runtime
kubectl -n memory-app exec deployment/memory-app-py312 -c memory-app -- printenv PYTHONUNBUFFERED PYTHONDONTWRITEBYTECODE
~~~

Expect **Runtime configuration and Secret validated** and both settings equal 1.
Repeat for py313 and py314.

Environment changes require container replacement to take effect consistently.
Update the ConfigMap and Pod templates through Git when changing configuration.
