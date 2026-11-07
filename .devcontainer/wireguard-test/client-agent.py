import hashlib
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

CONFIG = Path("/run/wireguard-client/client.conf")
STATUS = Path("/run/wireguard-client-status/client.json")
CONFIG_PATH = Path("/etc/wireguard/wg-client.conf")
INTERFACE = "wg-client"
ALLOWED_DIRECTIVES = {
    "Interface": {"PrivateKey", "Address", "MTU", "DNS", "FwMark", "Table"},
    "Peer": {
        "PublicKey",
        "PresharedKey",
        "AllowedIPs",
        "Endpoint",
        "PersistentKeepalive",
    },
}


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


def write_status(digest: str, success: bool, error: str | None = None) -> None:
    STATUS.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=STATUS.parent, prefix=".client-")
    try:
        os.fchmod(descriptor, 0o644)
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            json.dump(
                {"sha256": digest, "success": success, "error": error},
                file,
            )
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, STATUS)
    finally:
        Path(temporary).unlink(missing_ok=True)


def apply(config: str) -> None:
    if "[Interface]" not in config or "[Peer]" not in config:
        raise ValueError("Invalid client WireGuard configuration")
    validate_config(config)

    if (
        subprocess.run(
            ["ip", "link", "show", "dev", INTERFACE],
            capture_output=True,
            check=False,
        ).returncode
        == 0
    ):
        run_checked(["wg-quick", "down", str(CONFIG_PATH)])

    descriptor, temporary = tempfile.mkstemp(dir=CONFIG_PATH.parent, prefix=".wg-")
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            file.write(config)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, CONFIG_PATH)
    finally:
        Path(temporary).unlink(missing_ok=True)

    run_checked(["wg-quick", "up", str(CONFIG_PATH)])


def main() -> None:
    CONFIG_PATH.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    last_digest = None
    print("WireGuard test client ready; waiting for client.conf", flush=True)
    while True:
        try:
            config = CONFIG.read_text(encoding="utf-8")
        except FileNotFoundError:
            if last_digest is not None:
                subprocess.run(["wg-quick", "down", str(CONFIG_PATH)], check=False)
                last_digest = None
            time.sleep(0.5)
            continue

        digest = hashlib.sha256(config.encode()).hexdigest()
        if digest != last_digest:
            try:
                apply(config)
                last_digest = digest
                write_status(digest, True)
                print("Applied updated client config", flush=True)
            except (OSError, ValueError, RuntimeError) as error:
                write_status(digest, False, str(error))
                print(f"Client config apply failed: {error}", flush=True)
        time.sleep(0.5)


if __name__ == "__main__":
    main()
