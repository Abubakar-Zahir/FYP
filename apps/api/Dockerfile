# Production image for the API. Build from the repo root, because uv.lock and ml/ live there:
#   docker build -f apps/api/Dockerfile -t fyp-api .
FROM python:3.12.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

WORKDIR /srv

# Dependencies first, so code changes don't reinstall them.
# The video worker builds with UV_GROUPS="--group video" to add Whisper and OpenCV.
ARG UV_GROUPS=""
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-dev --no-install-project ${UV_GROUPS}

COPY apps/api ./apps/api
COPY ml ./ml

# Whisper downloads its model here on first use. The video worker keeps it in a volume.
ENV HF_HOME=/srv/models
RUN useradd --system --uid 10001 app && mkdir -p /srv/models && chown app /srv/models
USER app

EXPOSE 8000
# Caddy terminates HTTPS in front of this, so trust its forwarded headers.
CMD ["uvicorn", "app.main:app", "--app-dir", "apps/api", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
