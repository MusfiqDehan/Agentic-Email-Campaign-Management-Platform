# syntax=docker/dockerfile:1
# Optimized production image for Django ASGI (Daphne)
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /usr/src/app

# Install uv (fast installer) from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# System deps needed for building wheels (e.g. cryptography/psycopg)
# Keep `bash` (entrypoint) and `curl` (healthchecks) in the runtime image.
RUN apt-get update \
    && apt-get install -y --no-install-recommends bash curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt /usr/src/app/requirements.txt
RUN uv pip install --system --no-cache -r /usr/src/app/requirements.txt \
    && apt-get purge -y --auto-remove build-essential

# Copy app
COPY . /usr/src/app/

EXPOSE 8002

ENTRYPOINT ["bash", "deployments/docker_entrypoint.sh"]
CMD ["daphne", "-p", "8002", "-b", "0.0.0.0", "config.asgi:application"]

