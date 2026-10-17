FROM python:3.12-slim

WORKDIR /app

RUN groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid appuser --no-create-home appuser

COPY app/app.py ./app.py

USER 10001:10001

EXPOSE 8080

CMD ["python", "app.py"]