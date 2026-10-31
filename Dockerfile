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
