import asyncio
import re
import time

from loguru import logger

RECENT_HANDSHAKE_SECONDS = 180


def parse_wireguard_dump(output: str) -> dict[str, dict[str, int | str | None]]:
    lines = output.splitlines()
    if not lines or len(lines[0].split()) != 4:
        raise ValueError("Unexpected interface row in WireGuard dump")

    peers = {}
    for line in lines[1:]:
        fields = line.split()
        if len(fields) != 8:
            raise ValueError("Unexpected peer row in WireGuard dump")

        public_key, _, endpoint, _, handshake, received, transmitted, _ = fields
        try:
            handshake_timestamp = int(handshake)
            received_bytes = int(received)
            transmitted_bytes = int(transmitted)
        except ValueError as exc:
            raise ValueError("Invalid numeric field in WireGuard peer row") from exc

        peers[public_key] = {
            "Endpoint": None if endpoint == "(none)" else endpoint,
            "LastHandshake": handshake_timestamp or None,
            "ReceivedBytes": received_bytes,
            "TransmittedBytes": transmitted_bytes,
        }
    return peers


async def read_wireguard_status(
    interface: str, *, timeout: float = 10
) -> dict[str, dict[str, int | str | None]]:
    if not re.fullmatch(r"[A-Za-z0-9_=+.-]{1,15}", interface):
        raise ValueError("Invalid WireGuard interface name")

    process = await asyncio.create_subprocess_exec(
        "wg",
        "show",
        interface,
        "dump",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout)
    except (TimeoutError, asyncio.CancelledError):
        if process.returncode is None:
            process.kill()
        await process.communicate()
        raise

    if process.returncode:
        logger.error(
            "Could not read WireGuard status for {}: {}",
            interface,
            stderr.decode(errors="replace").strip(),
        )
        raise RuntimeError("WireGuard status command failed")

    return parse_wireguard_dump(stdout.decode(errors="strict"))


def is_recent_handshake(timestamp: int | None, *, now: int | None = None) -> bool:
    if timestamp is None:
        return False
    current_time = int(time.time()) if now is None else now
    age = current_time - timestamp
    return 0 <= age <= RECENT_HANDSHAKE_SECONDS
