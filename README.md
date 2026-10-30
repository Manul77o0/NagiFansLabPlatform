## NagiFans Lab PlatformProject

This project will serve multiple functions:

- AuthBase
- WebDAV (for Joplin)
- and more.

## How To DEBUG

```bash
uv run fastapi dev
```

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