FROM mcr.microsoft.com/dotnet/sdk:9.0-bookworm-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
        git cmake gcc g++ build-essential \
        libssl-dev libzmq3-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /build
RUN git clone https://github.com/oliverw/miningcore.git .

# Self-contained: bundles the correct .NET runtime so the image runtime version doesn't matter.
RUN dotnet publish src/Miningcore/Miningcore.csproj \
        -c Release \
        -r linux-x64 \
        --self-contained true \
        -o /app

FROM mcr.microsoft.com/dotnet/runtime-deps:9.0-bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        libzmq5 libsodium23 libgdiplus && \
    rm -rf /var/lib/apt/lists/*

ENV DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1

WORKDIR /app
COPY --from=builder /app .

RUN useradd -r -u 1000 -m bitcoin && chown -R bitcoin:bitcoin /app
USER bitcoin

ENTRYPOINT ["./Miningcore"]
CMD ["-c", "/app/config.json"]
