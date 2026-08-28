FROM debian:bookworm-slim

ARG VERSION=29.1.0
ARG TARGETARCH

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    ca-certificates \
    libssl3 \
    libevent-2.1-7 \
    libboost-filesystem1.81.0 \
    libboost-thread1.81.0 \
    libminiupnpc17 \
    && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    case "${TARGETARCH}" in \
      amd64) ARCH="x86_64" ;; \
      arm64) ARCH="aarch64" ;; \
      arm)   ARCH="arm-linux-gnueabihf" ;; \
      *)     echo "Unsupported arch: ${TARGETARCH}"; exit 1 ;; \
    esac; \
    wget -qO /tmp/btcii.tar.gz \
      "https://github.com/Bitcoin-II/BitcoinII-Core/releases/download/v${VERSION}/BitcoinII-${VERSION}-${ARCH}-linux-CLI.tar.gz"; \
    tar -xzf /tmp/btcii.tar.gz -C /tmp/; \
    install -m 755 "/tmp/BitcoinII-${VERSION}-${ARCH}-linux-CLI/bitcoinIId"    /usr/local/bin/bitcoinIId; \
    install -m 755 "/tmp/BitcoinII-${VERSION}-${ARCH}-linux-CLI/bitcoinII-cli" /usr/local/bin/bitcoinII-cli; \
    rm -rf /tmp/btcii*

RUN useradd -r -u 1000 -m -d /home/bitcoin bitcoin
USER bitcoin
WORKDIR /home/bitcoin

EXPOSE 9009 7009 8339

ENTRYPOINT ["bitcoinIId"]
