# Local integration tests

## MailCatcher

The Dev Container starts MailCatcher with Docker Compose. Open
<http://localhost:1080> to view captured email. Configure applications running
inside the Compose network to use `mail:1025` as their SMTP server.

## WireGuard local integration test

The devcontainer API writes generated server/client configs to the ignored
`.devcontainer/wireguard-test/data` directory. A separate Compose project runs
the server and client agents; only those containers receive `NET_ADMIN` and
`/dev/net/tun`. The API container does not receive network administration
capabilities or access to the Docker socket.

This test setup is opt-in. Rebuild/reopen the devcontainer after changing its
Compose configuration, then start the test containers from the repository root:

```bash
docker compose -f .devcontainer/wireguard-test.compose.yml up -d --build
```

In the UI, configure the server with interface `wg0`, listen port `51820`, and
address `10.77.0.1/24`. Set the global endpoint to
`wireguard-test-server:51820`. Create one enabled client with address
`10.77.0.2/32` and Allowed IPs `10.77.0.0/24`, then save settings and use
**サーバー設定を適用**. In test mode, server script hooks are intentionally
omitted because the WireGuard agent runs as root inside a network-capable
container. The server agent receives only its request/status directories; the
client agent receives only the client config and its status directory.
The apply request waits for both containers to report that `wg-quick up`
completed successfully.

Check the handshake and tunnel reachability:

```bash
docker compose -f .devcontainer/wireguard-test.compose.yml exec wireguard-test-client ping -c 3 10.77.0.1
docker compose -f .devcontainer/wireguard-test.compose.yml exec wireguard-test-server wg show wg0
docker compose -f .devcontainer/wireguard-test.compose.yml exec wireguard-test-client wg show wg-client
```

Stop and remove the test containers with:

```bash
docker compose -f .devcontainer/wireguard-test.compose.yml down
```

The shared test directory contains private keys and is git-ignored; keep it
local. The test containers use WireGuard-Go and require a host-provided
`/dev/net/tun` device (on Linux, `sudo modprobe tun` may be needed first).
This is a local integration harness, not a production deployment.
