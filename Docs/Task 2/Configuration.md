# Task 2: Runtime ConfigMap and BusyBox initContainer

Application source code and its original tests are unchanged.

The ConfigMap `memory-app-runtime` supplies two Python interpreter settings:

- `PYTHONUNBUFFERED: "1"` enables unbuffered stdout/stderr.
- `PYTHONDONTWRITEBYTECODE: "1"` prevents writing Python bytecode cache files.

Python reads these without changes to app.py or the Dockerfile. Our application
already flushes its logging handler; this is runtime configuration, not a fix
for a known missing-log problem.

Each Deployment uses `envFrom` to inject these settings into the app and its
`validate-runtime` initContainer. The initContainer uses the separate
`busybox:1.37.0-musl` image and checks both settings equal 1. It runs a shell
command and exits successfully before the app starts. Invalid settings produce
a nonzero exit and prevent startup. No external service, shared writable volume,
new endpoint, or API permission is introduced.

BusyBox runs as UID/GID 10001 with a read-only root filesystem, dropped Linux
capabilities, RuntimeDefault seccomp, and no privilege escalation. It requests
25m CPU/32Mi memory and is limited to 100m CPU/64Mi. These sequential init
resources are below the app's resources, so effective Pod requests and limits
remain unchanged.

CI scans the Python application images; the BusyBox initContainer image is not
scanned by this workflow. The application image updater targets only the GHCR
Python release image and leaves the independent BusyBox version unchanged.
BusyBox uses a pinned version tag, not a digest.

## Verify after GitOps sync

```bash
kubectl -n memory-app get configmap memory-app-runtime
kubectl -n memory-app get pods
kubectl -n memory-app logs deployment/memory-app-py312 -c validate-runtime
kubectl -n memory-app exec deployment/memory-app-py312 -c memory-app -- printenv PYTHONUNBUFFERED PYTHONDONTWRITEBYTECODE
```

Expected init log: `Runtime configuration validated`. Both environment values
should print 1. Repeat for py313 and py314. Use an explicit container name when
inspecting logs. The app's intentional memory leak and 400Mi limit are unchanged.

ConfigMap environment changes do not refresh running processes. Change the
ConfigMap and the Pod template (for example a configuration revision annotation)
in the same PR when replacing these settings. Current validation intentionally
requires both settings to remain enabled.

Secret integration is deferred until after Task 3.
