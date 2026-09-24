FROM debian:bookworm-slim

ARG VERSION=31.1.3
ARG TARGETARCH

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    ca-certificates \
    libssl3 \
    libevent-2.1-7 \
    libboost-filesystem1.81.0 \
    libboost-thread1.81.0 \
    && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    case "${TARGETARCH}" in \
      amd64) ARCH="x86_64" ;; \
      *) echo "Unsupported arch: ${TARGETARCH} — only linux/amd64 binaries are published for Bitcoin Silver"; exit 1 ;; \
    esac; \
    wget -qO /tmp/btcs.tar.gz \
      "https://github.com/bitcoin-silver/core/releases/download/version${VERSION}/bitcoinsilver-${VERSION}-${ARCH}-linux-gnu.tar.gz"; \
    tar -xzf /tmp/btcs.tar.gz -C /tmp/; \
    install -m 755 "/tmp/bitcoinsilver-${VERSION}-${ARCH}-linux-gnu/bin/bitcoinsilverd" /usr/local/bin/bitcoinsilverd; \
    install -m 755 "/tmp/bitcoinsilver-${VERSION}-${ARCH}-linux-gnu/bin/bitcoinsilver-cli" /usr/local/bin/bitcoinsilver-cli; \
    rm -rf /tmp/btcs*

RUN useradd -r -u 1000 -m -d /home/bitcoin bitcoin
USER bitcoin
WORKDIR /home/bitcoin

EXPOSE 9011 7011 10566

ENTRYPOINT ["bitcoinsilverd"]
