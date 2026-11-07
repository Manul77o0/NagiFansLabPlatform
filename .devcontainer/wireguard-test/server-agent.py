import json
import os
import re
import subprocess
import tempfile
import time
import traceback
from pathlib import Path

ROOT = Path("/run/wireguard-test")
REQUESTS = ROOT / "requests"
STATUSES = ROOT / "status"
INTERFACE_PATTERN = re.compile(r"[A-Za-z0-9_=+.-]{1,15}")
HOOK_PATTERN = re.compile(r"^\s*(PreUp|PostUp|PreDown|PostDown)\s*=", re.MULTILINE)
ALLOWED_DIRECTIVES = {
    "Interface": {"Address", "PrivateKey", "ListenPort"},
    "Peer": {"PublicKey", "PresharedKey", "AllowedIPs"},
}


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=".status-")
    try:
        os.fchmod(descriptor, 0o644)
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            json.dump(value, file)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def run_checked(command: list[str]) -> None:
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"{command[0]} failed")


def validate_config(config: str) -> None:
    section = None
    for line in config.splitlines():
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        if value.startswith("[") and value.endswith("]"):
            section = value[1:-1]
            if section not in ALLOWED_DIRECTIVES:
                raise ValueError(f"Unsupported WireGuard section: {section}")
            continue
        if section is None or "=" not in value:
            raise ValueError("Malformed WireGuard configuration line")
        key, directive_value = (part.strip() for part in value.split("=", 1))
        if key not in ALLOWED_DIRECTIVES[section] or not directive_value:
            raise ValueError(f"Unsupported WireGuard directive: {key}")


def apply(request: dict) -> None:
    request_id = request.get("id")
    interface = request.get("interface")
    config = request.get("config")
    if not isinstance(request_id, str) or not re.fullmatch(
        r"[a-f0-9-]{36}", request_id
    ):
        raise ValueError("Invalid request ID")
    if (
        not isinstance(interface, str)
        or interface in {".", ".."}
        or not INTERFACE_PATTERN.fullmatch(interface)
    ):
        raise ValueError("Invalid WireGuard interface name")
    if not isinstance(config, str) or "[Interface]" not in config:
        raise ValueError("Invalid WireGuard configuration")
    if HOOK_PATTERN.search(config):
        raise ValueError("Script hooks are disabled in the test container")
    validate_config(config)

    ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
    config_path = Path("/etc/wireguard") / f"{interface}.conf"
    config_path.parent.mkdir(mode=0o700, exist_ok=True)
    if (
        subprocess.run(
            ["ip", "link", "show", "dev", interface],
            capture_output=True,
            check=False,
        ).returncode
        == 0
    ):
        run_checked(["wg-quick", "down", str(config_path)])

    descriptor, temporary = tempfile.mkstemp(dir=config_path.parent, prefix=".wg-")
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            file.write(config)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, config_path)
    finally:
        Path(temporary).unlink(missing_ok=True)

    run_checked(["wg-quick", "up", str(config_path)])


def main() -> None:
    REQUESTS.mkdir(mode=0o700, parents=True, exist_ok=True)
    STATUSES.mkdir(mode=0o755, parents=True, exist_ok=True)
    STATUSES.chmod(0o755)
    print("WireGuard test apply agent ready", flush=True)
    while True:
        for request_path in sorted(REQUESTS.glob("*.json")):
            request_id = request_path.stem
            try:
                request = json.loads(request_path.read_text(encoding="utf-8"))
                if request.get("id") != request_id:
                    raise ValueError("Request ID does not match its filename")
                apply(request)
                write_json(
                    STATUSES / f"{request_id}.json",
                    {"id": request_id, "success": True},
                )
                print(f"Applied WireGuard config request {request_id}", flush=True)
            except (
                OSError,
                ValueError,
                json.JSONDecodeError,
                subprocess.CalledProcessError,
                RuntimeError,
            ) as error:
                write_json(
                    STATUSES / f"{request_id}.json",
                    {"id": request_id, "success": False, "error": str(error)},
                )
                print(f"WireGuard apply failed for {request_id}: {error}", flush=True)
            except Exception:
                write_json(
                    STATUSES / f"{request_id}.json",
                    {
                        "id": request_id,
                        "success": False,
                        "error": "Unexpected agent error",
                    },
                )
                traceback.print_exc()
            finally:
                request_path.unlink(missing_ok=True)
        time.sleep(0.2)


if __name__ == "__main__":
    main()
