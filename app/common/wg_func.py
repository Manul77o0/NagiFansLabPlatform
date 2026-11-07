import json
from collections.abc import Mapping
from typing import Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.common.schema import WGClient
from app.database import AsyncSession
from app.models import WireGuard


async def get_wireguard_data(
    db: AsyncSession, entry_type: str, name: str
) -> dict[str, Any] | None:
    result = await db.execute(
        select(WireGuard).where(
            WireGuard.type == entry_type,
            WireGuard.name == name,
        )
    )
    entry = result.scalar_one_or_none()
    return json.loads(entry.value) if entry is not None else None


async def save_wireguard_data(
    db: AsyncSession,
    entry_type: str,
    name: str,
    data: Mapping[str, Any],
    *,
    merge: bool = False,
) -> None:
    result = await db.execute(
        select(WireGuard).where(
            WireGuard.type == entry_type,
            WireGuard.name == name,
        )
    )
    entry = result.scalar_one_or_none()
    values = dict(data)

    if entry is None:
        entry = WireGuard(type=entry_type, name=name, value="")
        db.add(entry)
    elif merge:
        values = {**json.loads(entry.value), **values}

    entry.value = json.dumps(values, ensure_ascii=False, indent=4)

    try:
        await db.commit()
    except SQLAlchemyError:
        logger.exception("Failed to save WireGuard data ({}/{})", entry_type, name)
        await db.rollback()
        raise


def client_from_entry(entry: WireGuard) -> WGClient:
    values = json.loads(entry.value)
    return WGClient.model_validate({**values, "ID": entry.name})


async def get_client_by_uuid(db: AsyncSession, client_id: str) -> WGClient | None:
    result = await db.execute(
        select(WireGuard).where(
            WireGuard.type == "client",
            WireGuard.name == client_id,
        )
    )
    entry = result.scalar_one_or_none()
    return client_from_entry(entry) if entry is not None else None


async def get_all_clients(db: AsyncSession) -> list[WGClient]:
    entries = await get_all_client_data(db)
    return [WGClient.model_validate(entry) for entry in entries]


async def get_all_client_data(db: AsyncSession) -> list[dict[str, Any]]:
    result = await db.execute(
        select(WireGuard).where(WireGuard.type == "client").order_by(WireGuard.name)
    )
    return [
        {**json.loads(entry.value), "ID": entry.name}
        for entry in result.scalars().all()
    ]


async def update_client(
    db: AsyncSession, client_id: str, values: Mapping[str, Any]
) -> WGClient | None:
    client = await get_client_by_uuid(db, client_id)
    if client is None:
        return None

    client_values = client.model_dump(exclude={"ID"})
    client_values.update(values)
    await save_wireguard_data(db, "client", client_id, values, merge=True)
    return WGClient(ID=client_id, **client_values)
