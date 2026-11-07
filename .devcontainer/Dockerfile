FROM ghcr.io/astral-sh/uv:debian

RUN apt-get update \
    && apt-get install -y --no-install-recommends sqlite3 sudo \
    && rm -rf /var/lib/apt/lists/*
