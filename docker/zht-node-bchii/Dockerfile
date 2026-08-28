FROM fedora:40

ARG VERSION=27.0.2
ARG TARGETARCH

# Fedora 40 ships GCC 14 (GLIBCXX_3.4.32) and miniupnpc with soname 17 natively.
RUN dnf install -y --setopt=install_weak_deps=False \
        wget openssl-libs libevent miniupnpc libnatpmp zeromq sqlite-libs \
    && dnf clean all

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
