# NagiFans Lab Platform

FastAPI backend and Vue frontend for the NagiFans Lab platform.

## Run locally

Requirements: Python 3.12+, [uv](https://docs.astral.sh/uv/), and Node.js.

Start the API:

```bash
uv sync
uv run alembic upgrade head
uv run fastapi dev
```

In another terminal, start the frontend:

```bash
cd frontend
npm install
npm run dev
```

For local integration tests, see [docs/local-integration-tests.md](docs/local-integration-tests.md).

## Configuration and deployment

For local development over HTTP, set `COOKIE_SECURE=false`. Keep the default
secure cookie setting for HTTPS deployments.

Applying WireGuard settings writes a config under `/etc/wireguard` and restarts
the corresponding systemd service. Run the API on the host with only the
permissions it needs. WireGuard hooks run with `wg-quick` privileges, usually
root, so only trusted administrators should be able to change them. Applying
settings can interrupt active tunnels.

Browser sign-in uses an `HttpOnly` cookie; the browser does not store API tokens
in JavaScript. Use trusted email transport for client configuration emails:
they include private keys in both the `.conf` file and QR code.
