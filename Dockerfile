FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    HOME=/tmp/cvcannon-home

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        chromium \
        fonts-liberation \
        git \
        make \
        poppler-utils \
        python3 \
        webp \
    && rm -rf /var/lib/apt/lists/* \
    # Docker Desktop on Windows can present the bind mount with another owner,
    # which Git otherwise rejects as dubious ownership.
    && git config --system --add safe.directory /workspace

WORKDIR /workspace

CMD ["make", "help"]
