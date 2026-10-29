## NagiFans Lab PlatformProject

This project will serve multiple functions:

- AuthBase
- WebDAV (for Joplin)
- and more.

## How To DEBUG

```bash
uv run fastapi dev
```

## AutoGenerate DB Migrate
```bash
alembic revision --autogenerate -m "create tables"
```


## Run DB Migrate
```bash
alembic upgrade head
```

## SQLite debug maintenance

The SQLite maintenance endpoints are registered only when `DEBUG=true` is set
in the environment or `.env`. Keep the development server bound to localhost
while they are enabled.

- `GET /debug/sqlite/tables` lists application tables and row counts.
- `POST /debug/sqlite/vacuum` runs SQLite `VACUUM`.
- `GET /debug/sqlite/tables/{table}/rows?limit=100&offset=0` lists rows.
- `GET|PATCH|DELETE /debug/sqlite/tables/{table}/rows/{id}` reads, updates
  or deletes a row by its single-column primary key.
- `POST /debug/sqlite/tables/{table}/rows` creates a row from the JSON body
  `{"values": {"column": "value"}}` (`PATCH` takes the same body). Values are
  written as-is, so `users.password` must already be a hash.
- `POST /debug/sqlite/reset` deletes application data, preserving the
  `alembic_version` table. This destructive endpoint requires the JSON body
  `{"confirmation": "RESET DATABASE"}`.

For example:

```bash
curl -X POST http://127.0.0.1:8000/debug/sqlite/reset \
  -H 'Content-Type: application/json' \
  -d '{"confirmation": "RESET DATABASE"}'
```