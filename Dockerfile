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
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

CMD ["make", "help"]
