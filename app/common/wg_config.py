import base64
import binascii
import ipaddress
import re
import secrets
from collections.abc import Mapping, Sequence
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey


def _encode_key(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _decode_key(value: str, label: str) -> bytes:
    try:
        key = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(f"{label} must be a Base64-encoded WireGuard key") from exc
    if len(key) != 32:
        raise ValueError(f"{label} must decode to exactly 32 bytes")
    return key


def _public_from_private(private_key: bytes) -> bytes:
    return (
        X25519PrivateKey.from_private_bytes(private_key)
        .public_key()
        .public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
    )


def generate_keypair() -> dict[str, str]:
    private_key = bytearray(secrets.token_bytes(32))
    private_key[0] &= 248
    private_key[31] &= 127
    private_key[31] |= 64
    private_key_bytes = bytes(private_key)
    public_key_bytes = _public_from_private(private_key_bytes)
    return {
        "PrivateKey": _encode_key(private_key_bytes),
        "PublicKey": _encode_key(public_key_bytes),
    }


def generate_preshared_key() -> str:
    return _encode_key(secrets.token_bytes(32))


def prepare_client_keys(
    values: Mapping[str, Any],
    existing: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    merged = {**(existing or {}), **values}
    private_key = merged.get("PrivateKey")
    public_key = merged.get("PublicKey")
    result: dict[str, str] = {}

    if private_key:
        private_bytes = _decode_key(private_key, "Private key")
        derived = _public_from_private(private_bytes)
        result.update(
            PrivateKey=_encode_key(private_bytes),
            PublicKey=_encode_key(derived),
        )
    elif public_key:
        result["PublicKey"] = _encode_key(_decode_key(public_key, "Public key"))
    else:
        result.update(generate_keypair())

    preshared_key = merged.get("PresharedKey")
    result["PresharedKey"] = (
        _encode_key(_decode_key(preshared_key, "Preshared key"))
        if preshared_key
        else generate_preshared_key()
    )
    return result


def prepare_server_keys(
    values: Mapping[str, Any],
    existing: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    merged = {**(existing or {}), **values}
    private_key = merged.get("PrivateKey")
    if not private_key:
        return generate_keypair()
    private_bytes = _decode_key(private_key, "Server private key")
    return {
        "PrivateKey": _encode_key(private_bytes),
        "PublicKey": _encode_key(_public_from_private(private_bytes)),
    }


def _required_value(data: Mapping[str, Any], key: str, label: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} is required")
    value = value.strip()
    if "\n" in value or "\r" in value:
        raise ValueError(f"{label} must be a single line")
    return value


def _optional_value(data: Mapping[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()
    if "\n" in value or "\r" in value:
        raise ValueError(f"{key} must be a single line")
    return value or None


def _append_directive(lines: list[str], key: str, value: str | None) -> None:
    if value:
        lines.append(f"{key} = {value}")


def _script_lines(key: str, value: str | None) -> list[str]:
    if not value:
        return []
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    commands = [line.strip() for line in value.splitlines() if line.strip()]
    return [f"{key} = {command}" for command in commands]


def generate_client_config(
    client: Mapping[str, Any],
    server: Mapping[str, Any],
    global_settings: Mapping[str, Any],
) -> str:
    private_key = _encode_key(
        _decode_key(
            _required_value(client, "PrivateKey", "Client private key"),
            "Client private key",
        )
    )
    server_public_key = _encode_key(
        _decode_key(
            _required_value(server, "PublicKey", "Server public key"),
            "Server public key",
        )
    )
    endpoint = _required_value(global_settings, "Endpoint", "Global endpoint")
    address = _required_value(client, "IPAllocation", "Client IP allocation")
    allowed_ips = _required_value(client, "AllowedIPs", "Client allowed IPs")

    lines = ["[Interface]", f"PrivateKey = {private_key}", f"Address = {address}"]
    mtu = global_settings.get("MTU")
    if mtu is not None:
        _append_directive(lines, "MTU", str(mtu))
    if client.get("UseDNS"):
        dns_server = _required_value(global_settings, "DNSServer", "Global DNS server")
        _append_directive(lines, "DNS", dns_server)
    _append_directive(lines, "FwMark", _optional_value(global_settings, "FirewallMark"))
    _append_directive(lines, "Table", _optional_value(global_settings, "Table"))

    lines.extend(["", "[Peer]", f"PublicKey = {server_public_key}"])
    preshared_key = _optional_value(client, "PresharedKey")
    if preshared_key:
        preshared_key = _encode_key(_decode_key(preshared_key, "Preshared key"))
    _append_directive(lines, "PresharedKey", preshared_key)
    lines.extend([f"AllowedIPs = {allowed_ips}", f"Endpoint = {endpoint}"])

    keepalive = global_settings.get("PersistentKeepalive")
    if keepalive:
        _append_directive(lines, "PersistentKeepalive", str(keepalive))

    return "\n".join(lines) + "\n"


def generate_server_config(
    server: Mapping[str, Any],
    clients: Sequence[Mapping[str, Any]],
    *,
    include_scripts: bool = True,
) -> tuple[str, str, int]:
    interface = _required_value(server, "ServerInterface", "Server interface")
    if interface in {".", ".."} or not re.fullmatch(
        r"[A-Za-z0-9_=+.-]{1,15}", interface
    ):
        raise ValueError("Server interface must be a valid Linux interface name")
    address = _required_value(server, "Address", "Server address")
    try:
        for value in address.split(","):
            ipaddress.ip_interface(value.strip())
    except ValueError as exc:
        raise ValueError(
            "Server address must contain valid IP addresses with prefixes"
        ) from exc
    private_key = _encode_key(
        _decode_key(
            _required_value(server, "PrivateKey", "Server private key"),
            "Server private key",
        )
    )
    listen_port = server.get("ListenPort")
    if not isinstance(listen_port, int) or not 1 <= listen_port <= 65535:
        raise ValueError("Server listen port must be between 1 and 65535")

    lines = [
        "[Interface]",
        f"Address = {address}",
        f"PrivateKey = {private_key}",
        f"ListenPort = {listen_port}",
    ]
    if include_scripts:
        for key in ("PostUpScript", "PreDownScript", "PostDownScript"):
            directive = key.removesuffix("Script")
            lines.extend(_script_lines(directive, server.get(key)))

    peers = 0
    for client in clients:
        if client.get("disabled"):
            continue
        client_name = str(client.get("Name") or "Unnamed client")
        public_key = _encode_key(
            _decode_key(
                _required_value(client, "PublicKey", f"{client_name} public key"),
                f"{client_name} public key",
            )
        )
        ip_allocation = _required_value(
            client, "IPAllocation", f"{client_name} IP allocation"
        )
        lines.extend(["", "[Peer]", f"PublicKey = {public_key}"])
        preshared_key = _optional_value(client, "PresharedKey")
        if preshared_key:
            preshared_key = _encode_key(_decode_key(preshared_key, "Preshared key"))
        _append_directive(lines, "PresharedKey", preshared_key)
        lines.append(f"AllowedIPs = {ip_allocation}")
        peers += 1

    return "\n".join(lines) + "\n", interface, peers
