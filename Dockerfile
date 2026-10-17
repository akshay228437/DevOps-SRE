FROM python:3.12-alpine

WORKDIR /app

RUN addgroup -g 10001 appuser \
    && adduser -D -H -u 10001 -G appuser appuser

COPY app/app.py ./app.py

USER 10001:10001

EXPOSE 8080

CMD ["python", "app.py"]