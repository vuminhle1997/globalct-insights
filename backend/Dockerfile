FROM debian:bookworm-slim AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    bzip2 \
    ca-certificates \
    curl \
    freetds-dev \
    gawk \
    git \
    libsqlite3-dev \
    libssl3 \
    libzip-dev \
    make \
    openssl \
    patch \
    sbcl \
    time \
    unzip \
    wget \
    cl-ironclad \
    cl-babel \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/dimitri/pgloader.git /opt/src/pgloader

ARG DYNSIZE=16384

RUN mkdir -p /opt/src/pgloader/build/bin \
    && cd /opt/src/pgloader \
    && make DYNSIZE=$DYNSIZE clones save

FROM python:3.12-slim-bookworm

ENV POETRY_VERSION=2.1.4 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    freetds-dev \
    gawk \
    libsqlite3-dev \
    libzip-dev \
    make \
    sbcl \
    unzip \
    python3 \
    python3-pip \
    python3-venv \
    && update-ca-certificates \
    && pip install --no-cache-dir "poetry==${POETRY_VERSION}" \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/src/pgloader/build/bin/pgloader /usr/local/bin

WORKDIR /var/app/backend

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --only main --no-ansi

COPY . ./
RUN mkdir -p /var/app/backend/uploads/avatars

ENV PYTHONPATH=/var/app/backend
ENV PORT=4000
EXPOSE ${PORT}

# CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}
# CMD granian --interface asgi --host 0.0.0.0 --port ${PORT} main:app
CMD hypercorn main:app --bind 0.0.0.0:${PORT}

