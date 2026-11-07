import os
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Response, status
from loguru import logger
from pydantic import EmailStr, TypeAdapter, ValidationError
from qrcode.exceptions import DataOverflowError

from app.common.auth_func import check_admin, check_write, get_current_active_user
from app.common.email import create_qr_attachment, create_text_attachment, send_email
from app.common.schema import (
    Result,
    UpdateWGClient,
    WGClient,
    WGClientCreate,
    WGClientCreated,
    WGClientKeys,
    WGGlobal,
    WGPeerStatus,
    WGServer,
    WGServerApplyResult,
    WGServerKeys,
)
from app.common.wg_apply import (
    apply_systemd_config,
    apply_test_container_config,
    wait_for_test_client_config,
    write_test_client_config,
    write_test_config,
)
from app.common.wg_config import (
    generate_client_config,
    generate_keypair,
    generate_preshared_key,
    generate_server_config,
    prepare_client_keys,
    prepare_server_keys,
)
from app.common.wg_func import (
    get_all_client_data,
    get_wireguard_data,
    save_wireguard_data,
)
from app.common.wg_func import (
    get_all_clients as load_all_clients,
)
from app.common.wg_func import (
    update_client as save_client_update,
)
from app.common.wg_status import is_recent_handshake, read_wireguard_status
from app.database import AsyncSession, get_db

app = APIRouter(prefix="/wg_tools", tags=["WireGuardTools"])


@app.get("/global_settings", dependencies=[Depends(get_current_active_user)])
async def get_global_settings(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WGGlobal | None:
    config = await get_wireguard_data(db, "config", "global")
    return WGGlobal.model_validate(config) if config is not None else None


@app.post("/global_settings", dependencies=[Depends(check_write)])
async def post_global_settings(
    request: WGGlobal,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Result:
    await save_wireguard_data(db, "config", "global", request.model_dump())
    return Result(result="success")


@app.get("/server_settings", dependencies=[Depends(get_current_active_user)])
async def get_server_settings(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WGServer | None:
    config = await get_wireguard_data(db, "config", "server")
    if config is None:
        return None

    config.pop("PrivateKey", None)
    return WGServer.model_validate(config)


@app.post("/server_settings", dependencies=[Depends(check_write)])
async def post_server_settings(
    request: WGServer,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Result:
    config = await get_wireguard_data(db, "config", "server") or {}
    values = request.model_dump(exclude_unset=True)
    try:
        keys = prepare_server_keys(values, config)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    await save_wireguard_data(
        db,
        "config",
        "server",
        {**values, **keys},
        merge=True,
    )
    return Result(result="success")


@app.put("/server_settings/keys", dependencies=[Depends(check_write)])
async def update_server_keys(
    request: WGServerKeys,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Result:
    config = await get_wireguard_data(db, "config", "server")
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server settings not found",
        )
    values = {
        key: value
        for key, value in request.model_dump(exclude_unset=True).items()
        if value
    }
    try:
        keys = prepare_server_keys(values, config)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    await save_wireguard_data(db, "config", "server", keys, merge=True)
    return Result(result="success")


@app.get("/server_settings/keys", dependencies=[Depends(check_admin)])
async def get_server_keys(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WGServerKeys:
    server = await get_wireguard_data(db, "config", "server")
    if server is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server settings not found",
        )
    return WGServerKeys.model_validate(server)


@app.post("/server_settings/keys/generate", dependencies=[Depends(check_admin)])
async def generate_server_keys() -> WGClientKeys:
    return WGClientKeys(**generate_keypair())


@app.get("/clients", dependencies=[Depends(get_current_active_user)])
async def get_all_clients(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[WGClient]:
    return await load_all_clients(db)


@app.get("/connected_peers", dependencies=[Depends(check_admin)])
async def get_connected_peers(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[WGPeerStatus]:
    server = await get_wireguard_data(db, "config", "server")
    interface = server.get("ServerInterface") if server is not None else None
    if not isinstance(interface, str) or not interface:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="WireGuard server interface is not configured",
        )

    try:
        live_peers = await read_wireguard_status(interface)
    except (OSError, RuntimeError, TimeoutError, UnicodeError, ValueError) as exc:
        logger.exception("Could not retrieve connected WireGuard peers")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not retrieve WireGuard status; check the interface and server permissions",
        ) from exc

    peers = []
    for client in await get_all_client_data(db):
        status_data = live_peers.get(client.get("PublicKey"), {})
        handshake = status_data.get("LastHandshake")
        peers.append(
            WGPeerStatus(
                ID=client["ID"],
                Name=client["Name"],
                Email=client["Email"],
                IPAllocation=client.get("IPAllocation"),
                PublicKey=client.get("PublicKey"),
                Endpoint=status_data.get("Endpoint"),
                ReceivedBytes=status_data.get("ReceivedBytes") or 0,
                TransmittedBytes=status_data.get("TransmittedBytes") or 0,
                LastHandshake=handshake,
                Connected=is_recent_handshake(handshake),
            )
        )
    return sorted(peers, key=lambda peer: (peer.Name.casefold(), peer.ID))


@app.post("/client/register", dependencies=[Depends(check_write)])
async def register_client(
    request: WGClientCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WGClientCreated:
    values = request.model_dump()
    try:
        keys = prepare_client_keys(values)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    client_id = str(uuid4())
    await save_wireguard_data(db, "client", client_id, {**values, **keys})
    return WGClientCreated(ID=client_id)


@app.post("/client/generate-keys", dependencies=[Depends(check_admin)])
async def generate_new_client_keys() -> WGClientKeys:
    return WGClientKeys(**generate_keypair(), PresharedKey=generate_preshared_key())


async def get_client_config(db: AsyncSession, client_id: str) -> tuple[dict, str]:
    client = await get_wireguard_data(db, "client", client_id)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )
    if client.get("disabled"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Disabled clients cannot receive configuration files",
        )

    server = await get_wireguard_data(db, "config", "server")
    global_settings = await get_wireguard_data(db, "config", "global")
    if server is None or global_settings is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="WireGuard server and global settings must be configured first",
        )

    try:
        config = generate_client_config(client, server, global_settings)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return client, config


@app.get("/clients/{client_id}/config", dependencies=[Depends(check_admin)])
async def download_client_config(
    client_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    _, config = await get_client_config(db, client_id)
    return Response(
        content=config,
        media_type="text/plain",
        headers={
            "Content-Disposition": 'attachment; filename="wireguard-client.conf"',
            "Cache-Control": "no-store",
        },
    )


@app.post("/clients/{client_id}/send-config", dependencies=[Depends(check_admin)])
async def email_client_config(
    client_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Result:
    client, config = await get_client_config(db, client_id)
    email = client.get("Email")
    if not isinstance(email, str) or not email.strip():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Client email address is not configured",
        )
    try:
        recipient = TypeAdapter(EmailStr).validate_python(email)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Client email address is invalid",
        ) from exc

    try:
        qr_attachment = create_qr_attachment("wireguard-client-qr.png", config)
    except DataOverflowError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Client configuration is too large to encode as a QR code",
        ) from exc
    attachment = create_text_attachment("wireguard-client.conf", config)
    await send_email(
        [str(recipient)],
        "WireGuard クライアント設定",
        "WireGuardのクライアント設定ファイルとQRコードを添付します。"
        "どちらも秘密鍵を含むため、安全に保管してください。",
        attachments=[attachment, qr_attachment],
    )
    return Result(result="success")


@app.post("/server/apply", dependencies=[Depends(check_admin)])
async def apply_server_config(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WGServerApplyResult:
    server = await get_wireguard_data(db, "config", "server")
    if server is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Server settings must be configured first",
        )

    clients = await get_all_client_data(db)
    test_apply_dir = os.getenv("WG_TEST_APPLY_DIR")
    try:
        server_config, interface, peer_count = generate_server_config(
            server,
            clients,
            include_scripts=test_apply_dir is None,
        )
        test_client_config = None
        if test_apply_dir is not None:
            active_clients = [
                client for client in clients if not client.get("disabled")
            ]
            if active_clients:
                global_settings = await get_wireguard_data(db, "config", "global")
                if global_settings is None:
                    raise ValueError(
                        "Global settings must be configured before applying clients"
                    )
                test_client_config = generate_client_config(
                    active_clients[0],
                    server,
                    global_settings,
                )
                test_client_config += f"# test-apply-id = {uuid4()}\n"
    except (KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if test_apply_dir is not None:
        config_dir = Path(test_apply_dir)
        if not config_dir.is_absolute():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="WG_TEST_APPLY_DIR must be an absolute path",
            )
        try:
            write_test_config(config_dir, "server.conf", server_config)
            await apply_test_container_config(config_dir, interface, server_config)
            if test_client_config is None:
                (config_dir / "clients" / "client.conf").unlink(missing_ok=True)
            else:
                write_test_client_config(config_dir, test_client_config)
                await wait_for_test_client_config(config_dir, test_client_config)
        except TimeoutError as exc:
            logger.error("Timed out applying WireGuard test config for {}", interface)
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Timed out waiting for the WireGuard test server or client container",
            ) from exc
        except RuntimeError as exc:
            logger.error(
                "WireGuard test container failed to apply {}: {}", interface, exc
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"WireGuard test container failed to apply config: {exc}",
            ) from exc
        except OSError as exc:
            logger.exception("Could not write WireGuard test config for {}", interface)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not access the WireGuard test config directory",
            ) from exc

        return WGServerApplyResult(
            result="applied",
            mode="test-container",
            interface=interface,
            peer_count=peer_count,
        )

    try:
        await apply_systemd_config(interface, server_config)
    except TimeoutError as exc:
        logger.error("Timed out restarting WireGuard service for {}", interface)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Timed out restarting the WireGuard service; check its status",
        ) from exc
    except (OSError, RuntimeError) as exc:
        logger.error("Could not apply WireGuard config for {}: {}", interface, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not write or apply the WireGuard config; check server logs",
        ) from exc

    return WGServerApplyResult(
        result="applied",
        mode="systemd",
        interface=interface,
        peer_count=peer_count,
    )


@app.get("/clients/{client_id}/keys", dependencies=[Depends(check_admin)])
async def get_client_keys(
    client_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WGClientKeys:
    client_data = await get_wireguard_data(db, "client", client_id)
    if client_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )
    return WGClientKeys.model_validate(client_data)


@app.put("/clients/{client_id}/keys", dependencies=[Depends(check_write)])
async def update_client_keys(
    client_id: str,
    request: WGClientKeys,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Result:
    client_data = await get_wireguard_data(db, "client", client_id)
    if client_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )
    values = {
        key: value
        for key, value in request.model_dump(exclude_unset=True).items()
        if value
    }
    try:
        keys = prepare_client_keys(values, client_data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    await save_wireguard_data(db, "client", client_id, keys, merge=True)
    return Result(result="success")


async def set_client_status(db: AsyncSession, client_id: str, disabled: bool) -> Result:
    client = await save_client_update(db, client_id, {"disabled": disabled})
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )
    return Result(result="success")


@app.post("/{client_id}/enable", dependencies=[Depends(check_write)])
async def enable_client(
    client_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Result:
    return await set_client_status(db, client_id, False)


@app.post("/{client_id}/disable", dependencies=[Depends(check_write)])
async def disable_client(
    client_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Result:
    return await set_client_status(db, client_id, True)


@app.post("/{client_id}/update", dependencies=[Depends(check_write)])
async def update_client(
    client_id: str,
    request: UpdateWGClient,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Result:
    client = await save_client_update(
        db, client_id, request.model_dump(exclude_unset=True)
    )
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )
    return Result(result="success")
