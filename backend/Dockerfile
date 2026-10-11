# API and bot (the bot service runs the same image with another command).
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ffmpeg converts the videos uploaded in the admin panel (app/content_media.py).
RUN apt-get update     && apt-get install -y --no-install-recommends ffmpeg     && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml ./
COPY app ./app
RUN pip install .
COPY alembic.ini ./
COPY alembic ./alembic

# Not root inside the container. Uploaded pictures and videos go to /data/media
# (deploy/media on the server, owned by this user id).
RUN useradd --system --uid 10001 --no-create-home ekoustoz     && mkdir -p /data/media && chown ekoustoz /data/media
USER ekoustoz

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4)"

# Migrations first, then the API. Caddy in front passes the real client address
# (X-Forwarded-For); the API port is reachable only inside the compose network.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips '*' --no-server-header"]
