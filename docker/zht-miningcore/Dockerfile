FROM mcr.microsoft.com/dotnet/sdk:10.0-bookworm-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
        git cmake gcc g++ build-essential \
        libssl-dev libzmq3-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /build
RUN git clone https://github.com/oliverw/miningcore.git .

RUN find . -name "*.csproj" && \
    dotnet publish src/Miningcore/Miningcore.csproj \
        -c Release \
        -o /app \
        --self-contained false

FROM mcr.microsoft.com/dotnet/runtime:10.0-bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        libzmq5 libsodium23 libgdiplus && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /app .

RUN useradd -r -u 1000 -m bitcoin && chown -R bitcoin:bitcoin /app
USER bitcoin

ENTRYPOINT ["dotnet", "Miningcore.dll"]
CMD ["-c", "/app/config.json"]
