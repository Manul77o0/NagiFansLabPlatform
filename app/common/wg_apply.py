import asyncio
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from uuid import uuid4

WIREGUARD_CONFIG_DIR = Path("/etc/wireguard")


def _write_private_file(
    path: Path, content: str, *, manage_directory: bool = True
) -> None:
    if manage_directory:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(path.parent, 0o700)
    descriptor, temporary_path = tempfile.mkstemp(dir=path.parent, prefix=".wg-")
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_path, path)
    finally:
        Path(temporary_path).unlink(missing_ok=True)


async def apply_systemd_config(
    interface: str, config: str, *, timeout: float = 60
) -> None:
    if interface in {".", ".."} or not re.fullmatch(
        r"[A-Za-z0-9_=+.-]{1,15}", interface
    ):
        raise ValueError("Invalid WireGuard interface name")

    _write_private_file(
        WIREGUARD_CONFIG_DIR / f"{interface}.conf", config, manage_directory=False
    )
    process = await asyncio.create_subprocess_exec(
        "systemctl",
        "--no-ask-password",
        "restart",
        f"wg-quick@{interface}.service",
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        _, stderr = await asyncio.wait_for(process.communicate(), timeout)
    except (TimeoutError, asyncio.CancelledError):
        if process.returncode is None:
            process.kill()
        await process.communicate()
        raise
    if process.returncode:
        raise RuntimeError(
            f"systemctl restart failed: {stderr.decode(errors='replace').strip()}"
        )


async def apply_test_container_config(
    config_dir: Path,
    interface: str,
    config: str,
    *,
    timeout: float = 20,
) -> None:
    request_id = str(uuid4())
    request_path = config_dir / "requests" / f"{request_id}.json"
    status_path = config_dir / "status" / f"{request_id}.json"
    status_path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    request = json.dumps({"id": request_id, "interface": interface, "config": config})
    _write_private_file(request_path, request)

    try:
        deadline = asyncio.get_running_loop().time() + timeout
        while asyncio.get_running_loop().time() < deadline:
            if status_path.exists():
                result = json.loads(status_path.read_text(encoding="utf-8"))
                if result.get("id") != request_id:
                    raise RuntimeError(
                        "WireGuard test agent returned a mismatched status"
                    )
                if not result.get("success"):
                    raise RuntimeError(
                        result.get(
                            "error", "WireGuard test agent failed to apply config"
                        )
                    )
                return
            await asyncio.sleep(0.2)
        raise TimeoutError("Timed out waiting for the WireGuard test container")
    finally:
        request_path.unlink(missing_ok=True)
        status_path.unlink(missing_ok=True)


async def wait_for_test_client_config(
    config_dir: Path,
    config: str,
    *,
    timeout: float = 20,
) -> None:
    status_path = config_dir / "client-status" / "client.json"
    expected_digest = hashlib.sha256(config.encode()).hexdigest()
    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        if status_path.exists():
            result = json.loads(status_path.read_text(encoding="utf-8"))
            if result.get("sha256") == expected_digest:
                if not result.get("success"):
                    raise RuntimeError(
                        result.get(
                            "error", "WireGuard test client failed to apply config"
                        )
                    )
                return
        await asyncio.sleep(0.2)
    raise TimeoutError("Timed out waiting for the WireGuard test client")


def write_test_config(config_dir: Path, filename: str, config: str) -> None:
    if Path(filename).name != filename:
        raise ValueError("Test config filename must not contain a path")
    _write_private_file(config_dir / filename, config)


def write_test_client_config(config_dir: Path, config: str) -> None:
    _write_private_file(config_dir / "clients" / "client.conf", config)
