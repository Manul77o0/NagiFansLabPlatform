## NagiFans Lab PlatformProject

This project will serve multiple functions:

- AuthBase
- and more.

## How To DEBUG

```bash
uv run fastapi dev
```

See [local integration tests](docs/local-integration-tests.md) for MailCatcher
and WireGuard test instructions.

For a non-container Ubuntu 24.04 deployment and initial administrator setup,
see [production deployment](docs/production-ubuntu.md).

## WireGuard production application

When `WG_TEST_APPLY_DIR` is unset, applying server settings writes
`/etc/wireguard/<interface>.conf` with mode `0600`, then runs
`systemctl --no-ask-password restart wg-quick@<interface>.service`. The API
must run on the systemd host with permission to write that existing directory and
restart the unit without an interactive prompt. Install WireGuard and the
`wg-quick@.service` unit beforehand, and restrict directory access to trusted
users. A service restart may interrupt active
tunnels. The API reports a failure if writing or restarting fails; the new
file may already be on disk, and the service may be stopped or still changing
after a failure or timeout. Check its status and restore a known-good config
manually if necessary.

The configured server hooks execute with the privileges of `wg-quick` (usually
root). Users with write access can change these hooks, which execute when an
administrator applies the settings. Grant WireGuard write and admin access
only to trusted users; protect the API and config directory accordingly.
`systemctl` cannot control a separate host from an ordinary container; do not
give the API container the Docker socket or broad host privileges as a
workaround. The devcontainer explicitly selects the test-container backend.

The administrator-only `/wg_tools/connected_peers` view reads runtime details
with `wg show <interface> dump` on the API host. The API process must be able to
query the configured WireGuard interface; the view lists registered clients
and estimates connectivity from a handshake within the last three minutes.

Client configuration emails include a `.conf` file and a PNG QR code. The QR
code omits the Linux-specific `FwMark` and `Table` directives, which remain in
the `.conf` file when configured. Both contain private keys: use a trusted mail
transport, verify the recipient, and store or delete both attachments securely.

## Authentication

`POST /token` returns a Bearer access token for API clients. The browser UI is served as a static page and calls APIs directly: it signs in with `POST /session/login` using JSON credentials, which sets an `HttpOnly`, `SameSite=Lax` cookie, then loads `/users/me/` and `/users/me/items/`. `POST /session/logout` clears the cookie. The browser never reads or stores the token in JavaScript. Bearer tokens take precedence when both credentials are present.

The cookie is `Secure` by default. For local development over plain HTTP, set `COOKIE_SECURE=false`; use HTTPS and leave it enabled outside local development. Cookie-authenticated write endpoints should also enforce CSRF protection before they are added.

## AutoGenerate DB Migrate
```bash
alembic revision --autogenerate -m "create tables"
```


## Run DB Migrate
```bash
alembic upgrade head
```

## SQLite Command

Oneline Mode
```bash
$ sqlite3 -header -column test.db "SELECT * FROM users;"
```

Diag Mode
```bash
$ sqlite3 test.db
SQLite version 3.46.1 2024-08-13 09:16:08
Enter ".help" for usage hints.
sqlite> .headers on
sqlite> .mode column
sqlite> SELECT * FROM users;
id  name  level  email             password                                                      disabled
--  ----  -----  ----------------  ------------------------------------------------------------  --------              
sqlite> .quit
```
