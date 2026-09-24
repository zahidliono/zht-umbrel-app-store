FROM debian:bookworm-slim

ARG VERSION=1.21.3.0
ARG TARGETARCH

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    ca-certificates \
    unzip \
    libssl3 \
    libevent-2.1-7 \
    libboost-filesystem1.81.0 \
    libboost-thread1.81.0 \
    && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    case "${TARGETARCH}" in \
      amd64) ARCH="x86_64" ;; \
      arm64) ARCH="aarch64" ;; \
      *) echo "Unsupported arch: ${TARGETARCH}"; exit 1 ;; \
    esac; \
    wget -qO /tmp/wjk.zip \
      "https://github.com/WojakCoinProj/wojakcore/releases/download/${VERSION}/wojakcore-${VERSION}-linux-${ARCH}.zip"; \
    unzip -p /tmp/wjk.zip "wojakcoind-linux-${ARCH}" > /usr/local/bin/wojakcoind; \
    chmod 755 /usr/local/bin/wojakcoind; \
    rm -f /tmp/wjk.zip

RUN useradd -r -u 1000 -m -d /home/bitcoin bitcoin
USER bitcoin
WORKDIR /home/bitcoin

EXPOSE 9012 7012 20759

ENTRYPOINT ["wojakcoind"]
