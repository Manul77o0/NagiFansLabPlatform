from typing import Annotated, Any

from fastapi import APIRouter, Body, HTTPException, Query
from sqlalchemy import MetaData, Table, delete, insert, inspect, select, update
from sqlalchemy.engine import Connection, Row
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.database import engine

router = APIRouter(prefix="/debug/sqlite", tags=["debug"])


def _require_sqlite() -> None:
    if engine.url.get_backend_name() != "sqlite":
        raise HTTPException(
            status_code=409,
            detail="SQLite maintenance endpoints require a SQLite DATABASE_URL.",
        )


def _get_table_counts(connection: Connection) -> dict[str, int]:
    inspector = inspect(connection)
    table_counts = {}
    for table_name in inspector.get_table_names():
        if table_name.startswith("sqlite_"):
            continue
        quoted_table_name = connection.dialect.identifier_preparer.quote(table_name)
        table_counts[table_name] = connection.exec_driver_sql(
            f"SELECT COUNT(*) FROM {quoted_table_name}"
        ).scalar_one()
    return table_counts


def _load_table(connection: Connection, table_name: str) -> Table:
    if table_name not in inspect(connection).get_table_names():
        raise HTTPException(status_code=404, detail=f"Table not found: {table_name}")
    return Table(table_name, MetaData(), autoload_with=connection)


def _serialize_row(row: Row) -> dict[str, Any]:
    return {
        key: value.hex() if isinstance(value, bytes) else value
        for key, value in row._mapping.items()
    }


def _validate_values(table: Table, values: dict[str, Any]) -> None:
    if not values:
        raise HTTPException(status_code=422, detail="values must not be empty.")
    unknown_columns = sorted(set(values) - set(table.columns.keys()))
    if unknown_columns:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown columns: {', '.join(unknown_columns)}",
        )


def _primary_key_condition(table: Table, row_id: str):
    primary_key_columns = list(table.primary_key.columns)
    if len(primary_key_columns) != 1:
        raise HTTPException(
            status_code=409,
            detail="Row operations by id require a single-column primary key.",
        )
    column = primary_key_columns[0]
    try:
        value = column.type.python_type(row_id)
    except (NotImplementedError, ValueError) as err:
        raise HTTPException(status_code=422, detail="Invalid primary key value.") from err
    return column == value


@router.get("/tables")
async def list_tables() -> dict[str, dict[str, int]]:
    _require_sqlite()
    async with engine.connect() as connection:
        table_counts = await connection.run_sync(_get_table_counts)
    return {"tables": table_counts}


@router.get("/tables/{table_name}/rows")
async def list_rows(
    table_name: str,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict[str, Any]:
    _require_sqlite()
    async with engine.connect() as connection:
        table = await connection.run_sync(_load_table, table_name)
        result = await connection.execute(select(table).limit(limit).offset(offset))
        rows = [_serialize_row(row) for row in result]
    return {"rows": rows, "limit": limit, "offset": offset}


@router.get("/tables/{table_name}/rows/{row_id}")
async def get_row(table_name: str, row_id: str) -> dict[str, Any]:
    _require_sqlite()
    async with engine.connect() as connection:
        table = await connection.run_sync(_load_table, table_name)
        result = await connection.execute(
            select(table).where(_primary_key_condition(table, row_id))
        )
        row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Row not found.")
    return _serialize_row(row)


@router.post("/tables/{table_name}/rows", status_code=201)
async def create_row(
    table_name: str,
    values: Annotated[dict[str, Any], Body(embed=True)],
) -> dict[str, Any]:
    _require_sqlite()
    try:
        async with engine.begin() as connection:
            table = await connection.run_sync(_load_table, table_name)
            _validate_values(table, values)
            result = await connection.execute(insert(table).values(**values))
            primary_key = list(result.inserted_primary_key or [])
    except IntegrityError as err:
        raise HTTPException(status_code=409, detail=str(err.orig)) from err
    except SQLAlchemyError as err:
        raise HTTPException(status_code=422, detail=str(err)) from err
    return {"inserted_primary_key": primary_key}


@router.patch("/tables/{table_name}/rows/{row_id}")
async def update_row(
    table_name: str,
    row_id: str,
    values: Annotated[dict[str, Any], Body(embed=True)],
) -> dict[str, int]:
    _require_sqlite()
    try:
        async with engine.begin() as connection:
            table = await connection.run_sync(_load_table, table_name)
            _validate_values(table, values)
            result = await connection.execute(
                update(table).where(_primary_key_condition(table, row_id)).values(**values)
            )
    except IntegrityError as err:
        raise HTTPException(status_code=409, detail=str(err.orig)) from err
    except SQLAlchemyError as err:
        raise HTTPException(status_code=422, detail=str(err)) from err
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Row not found.")
    return {"updated": result.rowcount}


@router.delete("/tables/{table_name}/rows/{row_id}")
async def delete_row(table_name: str, row_id: str) -> dict[str, int]:
    _require_sqlite()
    async with engine.begin() as connection:
        table = await connection.run_sync(_load_table, table_name)
        result = await connection.execute(
            delete(table).where(_primary_key_condition(table, row_id))
        )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Row not found.")
    return {"deleted": result.rowcount}


@router.post("/vacuum")
async def vacuum_database() -> dict[str, str]:
    _require_sqlite()
    async with engine.connect() as connection:
        connection = await connection.execution_options(isolation_level="AUTOCOMMIT")
        await connection.exec_driver_sql("VACUUM")
    return {"status": "completed"}


@router.post("/reset")
async def reset_database(
    confirmation: Annotated[str, Body(embed=True)],
) -> dict[str, list[str]]:
    if confirmation != "RESET DATABASE":
        raise HTTPException(
            status_code=400,
            detail='Set confirmation to "RESET DATABASE" to delete all application data.',
        )
    _require_sqlite()

    async with engine.begin() as connection:
        table_counts = await connection.run_sync(_get_table_counts)
        tables_to_clear = [
            table_name
            for table_name in table_counts
            if table_name != "alembic_version"
        ]
        for table_name in reversed(tables_to_clear):
            quoted_table_name = connection.dialect.identifier_preparer.quote(table_name)
            await connection.exec_driver_sql(f"DELETE FROM {quoted_table_name}")

    return {"cleared_tables": tables_to_clear}
