FROM ubuntu:22.04

ARG VERSION=27.0.2
ARG TARGETARCH

ENV DEBIAN_FRONTEND=noninteractive

# ubuntu:22.04 has libminiupnpc17 (Noble/24.04 renamed it to libminiupnpc21).
# The toolchain PPA provides GCC 14's libstdc++6, which includes GLIBCXX_3.4.32.
RUN apt-get update && \
    apt-get install -y --no-install-recommends software-properties-common ca-certificates && \
    add-apt-repository -y ppa:ubuntu-toolchain-r/test && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        wget libssl3 libevent-2.1-7 libevent-pthreads-2.1-7 \
        libminiupnpc17 libnatpmp1 libzmq5 libsqlite3-0 libstdc++6 && \
    apt-get purge -y --auto-remove software-properties-common && \
    rm -rf /var/lib/apt/lists/*

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
