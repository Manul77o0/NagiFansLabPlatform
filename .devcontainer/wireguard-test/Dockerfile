FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        iproute2 \
        iputils-ping \
        python3 \
        wireguard-tools \
        wireguard-go \
    && rm -rf /var/lib/apt/lists/*

COPY server-agent.py client-agent.py /usr/local/bin/

CMD ["python3", "/usr/local/bin/server-agent.py"]
