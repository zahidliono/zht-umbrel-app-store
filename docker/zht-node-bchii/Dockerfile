FROM debian:bookworm-slim

ARG VERSION=27.0.2
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
      amd64) TARBALL="bitcoincashII-${VERSION}-linux64.tar.gz";        BINDIR="bitcoincashII-${VERSION}-linux64/bin" ;; \
      arm64) TARBALL="bitcoincashII-${VERSION}-linux-aarch64.tar.gz";  BINDIR="bitcoincashII-${VERSION}-linux-aarch64/bin" ;; \
      *)     echo "Unsupported arch: ${TARGETARCH}"; exit 1 ;; \
    esac; \
    wget -qO /tmp/bchii.tar.gz \
      "https://github.com/BitcoincashII/bitcoincashII-core/releases/download/v${VERSION}/${TARBALL}"; \
    tar -xzf /tmp/bchii.tar.gz -C /tmp/; \
    install -m 755 "/tmp/${BINDIR}/bitcoincashIId"    /usr/local/bin/bitcoincashIId; \
    install -m 755 "/tmp/${BINDIR}/bitcoincashII-cli" /usr/local/bin/bitcoincashII-cli; \
    rm -rf /tmp/bchii*

RUN useradd -r -u 1000 -m -d /home/bitcoin bitcoin
USER bitcoin
WORKDIR /home/bitcoin

EXPOSE 9010 7010 8340

ENTRYPOINT ["bitcoincashIId"]
