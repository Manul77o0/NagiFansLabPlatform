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