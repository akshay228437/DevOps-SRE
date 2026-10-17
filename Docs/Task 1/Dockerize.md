# Task 1.1: Dockerizing the Application

## Objective

Package the Python application in a small container that runs as a non-root user.

## Dockerfile

Place `Dockerfile` in the project root, beside `readme.md`.

```dockerfile# Task 1.1: Dockerizing the Application

## Objective

Package the Python application in a small container that runs as a non-root user.

## Dockerfile

Place `Dockerfile` in the project root, beside `readme.md`.

```dockerfile
FROM python:3.12-alpine

WORKDIR /app

RUN addgroup -g 10001 appuser \
    && adduser -D -H -u 10001 -G appuser appuser

COPY app/app.py ./app.py

USER 10001:10001

EXPOSE 8080

CMD ["python", "app.py"]
```

## Design Choices

- Used an Alpine-based Python image for a small runtime footprint.
- Selected Alpine after Trivy reported HIGH vulnerabilities in the previous Debian-based image. The Alpine image must also be scanned.
- Installed no additional Python packages because the application uses Python’s standard library.
- Copied only the application code into the image.
- Created a non-root user with UID and GID `10001` using Alpine’s `addgroup` and `adduser` commands.
- Documented port `8080` and configured Python as the startup process.

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

## Validation Status

The local Dockerfile uses Alpine. Successful build, health check, non-root execution, OOM termination, and vulnerability scan results remain to be confirmed from command output.