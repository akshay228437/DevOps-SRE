# Task 1.1: Dockerizing the Application

## Objective

Package the Python application in a small container that runs as a non-root user.

## Dockerfile

Place `Dockerfile` in the project root, beside `readme.md`.

```dockerfile
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-alpine

WORKDIR /app

RUN addgroup -g 10001 appuser \
    && adduser -D -H -u 10001 -G appuser appuser

COPY app/app.py ./app.py

USER 10001:10001

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/healthcheck', timeout=2).status == 200 else 1)"]

CMD ["python", "app.py"]
```

## Design Choices

- Used an Alpine-based Python image for a small runtime footprint.
- Selected Alpine after Trivy reported HIGH vulnerabilities in the previous Debian-based image. The Alpine image must also be scanned.
- Installed no additional Python packages because the application uses Python’s standard library.
- Copied only the application code into the image.
- Created a non-root user with UID and GID `10001` using Alpine’s `addgroup` and `adduser` commands.
- Documented port `8080` and configured Python as the startup process.
- Added a Docker health check using Python's standard library to call
  `/healthcheck` every 30 seconds, with a 2-second HTTP timeout, a 3-second
  command timeout, a 10-second startup grace period and three consecutive
  failures before marking the running container unhealthy. HTTP 200 succeeds;
  other responses or connection errors fail. No curl package is needed.
- Docker health status does not restart an unhealthy container by itself.
  Kubernetes uses the probes in the Deployments rather than this image health check.

## Build and Run

Run from the project root:

```powershell
docker build --pull -t memory-app:local .
docker run -d --name memory-app-check -p 8080:8080 --memory=400m --memory-swap=400m memory-app:local
```

The application intentionally increases memory usage. The container is limited to 400 MiB, with no additional swap allowance.

## Verification

Check the health endpoint shortly after startup:

```powershell
Invoke-RestMethod http://localhost:8080/healthcheck
```

Expected response: `status` is `healthy`.

After the first successful Docker health check, inspect its status:

```powershell
docker inspect memory-app-check --format '{{.State.Health.Status}}'
```

Expected while the app is serving: `healthy`. Immediately after startup it may
show `starting`. Rebuild the image to include Dockerfile health-check changes.

Check logs and the runtime user:

```powershell
docker logs memory-app-check
docker exec memory-app-check id
```

Expected: application logs and user ID `10001`.

After the memory limit is reached, inspect the stopped container:

```powershell
docker inspect memory-app-check --format 'Status={{.State.Status}} OOMKilled={{.State.OOMKilled}} ExitCode={{.State.ExitCode}}'
```

Expected: `Status=exited OOMKilled=true ExitCode=137`.

Remove the test container:

```powershell
docker rm -f memory-app-check
```

## Local Vulnerability Scan

Export the image and scan it using Trivy:

```powershell
docker save -o memory-app.tar memory-app:local

docker run --rm -v "${PWD}:/scan:ro" aquasec/trivy:latest image --input /scan/memory-app.tar --scanners vuln --severity HIGH,CRITICAL --exit-code 1
```

Review the scan output for vulnerabilities or scanner errors. Remove the exported file afterward:

```powershell
Remove-Item memory-app.tar
```

## Verification note

Alpine images were published and deployed through the pipeline. The intentional
OOM behavior was observed on Kubernetes. The newly added Docker HEALTHCHECK
still needs a rebuilt image and local Docker health-status verification.
