# Task 1.1: Dockerizing the Application

## Objective

Package the Python application in a small container that runs as a non-root user.

## Dockerfile

Place `Dockerfile` in the project root, beside `readme.md`.

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid appuser --no-create-home appuser

COPY app/app.py ./app.py

USER 10001:10001

EXPOSE 8080

CMD ["python", "app.py"]
```

## Design Choices

- Used a slim Python base image to reduce image size.
- Installed no additional packages because the application uses Python’s standard library.
- Copied only the application code into the image.
- Configured a non-root user with UID and GID `10001`.
- Documented port `8080` and configured Python as the startup process.

## Build and Run

Run from the project root:

```powershell
docker build -t memory-app:local .
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

## Validation Status

The Dockerfile and verification commands were reviewed. Successful build, health check, non-root execution, and OOM termination must be confirmed from local command output.