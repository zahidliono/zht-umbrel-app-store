FROM python:3.12-alpine
WORKDIR /app
COPY stratum.py .
RUN adduser -D -u 1000 bitcoin
USER bitcoin
ENTRYPOINT ["python3", "-u", "stratum.py"]
