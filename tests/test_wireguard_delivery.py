import asyncio
import os
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, patch

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("DOMAIN", "example.com")
os.environ.setdefault("MAIL_FROM", "test@example.com")
os.environ.setdefault("MAIL_PORT", "1025")
os.environ.setdefault("MAIL_SERVER", "localhost")
os.environ.setdefault("MAIL_STARTTLS", "false")
os.environ.setdefault("MAIL_SSL_TLS", "false")
os.environ.setdefault("USE_CREDENTIALS", "false")
os.environ.setdefault("VALIDATE_CERTS", "false")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from fastapi import HTTPException
from fastapi_mail import MessageSchema, MessageType
from fastapi_mail.msg import MailMsg
from PIL import Image, ImageChops
from qrcode import make
from qrcode.exceptions import DataOverflowError

from app.common import wg_apply
from app.common.wg_config import generate_client_config, generate_keypair
from app.routers import wgtools


class SystemdApplyTests(unittest.IsolatedAsyncioTestCase):
    async def test_writes_private_config_then_restarts_expected_service(self):
        """The config must exist with private permissions before systemctl runs."""
        with tempfile.TemporaryDirectory() as directory:
            config_dir = Path(directory)
            process = AsyncMock()
            process.communicate.return_value = (None, b"")
            process.returncode = 0

            async def start(*args, **kwargs):
                path = config_dir / "wg0.conf"
                self.assertEqual(path.read_text(), "config\n")
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
                self.assertEqual(
                    args,
                    (
                        "systemctl",
                        "--no-ask-password",
                        "restart",
                        "wg-quick@wg0.service",
                    ),
                )
                return process

            with (
                patch.object(wg_apply, "WIREGUARD_CONFIG_DIR", config_dir),
                patch.object(asyncio, "create_subprocess_exec", side_effect=start),
            ):
                await wg_apply.apply_systemd_config("wg0", "config\n")

    async def test_restart_failure_and_invalid_interface(self):
        """Restart errors propagate and invalid interface names are rejected."""
        with tempfile.TemporaryDirectory() as directory:
            process = AsyncMock()
            process.communicate.return_value = (None, b"unit failed")
            process.returncode = 1
            with (
                patch.object(wg_apply, "WIREGUARD_CONFIG_DIR", Path(directory)),
                patch.object(
                    asyncio, "create_subprocess_exec", AsyncMock(return_value=process)
                ) as start,
            ):
                with self.assertRaisesRegex(RuntimeError, "unit failed"):
                    await wg_apply.apply_systemd_config("wg0", "config\n")
                start.reset_mock()
                with self.assertRaises(ValueError):
                    await wg_apply.apply_systemd_config("../wg0", "config\n")
                start.assert_not_called()

    async def test_timeout_terminates_systemctl(self):
        """Timeouts terminate and reap the systemctl process."""
        with tempfile.TemporaryDirectory() as directory:
            process = AsyncMock()
            process.returncode = None
            process.kill = unittest.mock.Mock()

            async def communicate():
                if process.communicate.await_count == 1:
                    await asyncio.sleep(1)
                return None, b""

            process.communicate.side_effect = communicate
            with (
                patch.object(wg_apply, "WIREGUARD_CONFIG_DIR", Path(directory)),
                patch.object(
                    asyncio, "create_subprocess_exec", AsyncMock(return_value=process)
                ),
            ):
                with self.assertRaises(TimeoutError):
                    await wg_apply.apply_systemd_config("wg0", "config", timeout=0.01)
                process.kill.assert_called_once()


class WireGuardRouteTests(unittest.IsolatedAsyncioTestCase):
    async def test_production_apply_and_failure_response(self):
        """Production uses systemd and returns an error when the restart fails."""
        server = {
            **generate_keypair(),
            "ServerInterface": "wg0",
            "Address": "10.0.0.1/24",
            "ListenPort": 51820,
            "PostUpScript": "echo ready",
        }
        with (
            patch.dict(os.environ, {"WG_TEST_APPLY_DIR": ""}),
            patch.object(wgtools, "get_wireguard_data", AsyncMock(return_value=server)),
            patch.object(wgtools, "get_all_client_data", AsyncMock(return_value=[])),
            patch.object(wgtools, "apply_systemd_config", AsyncMock()) as apply,
        ):
            del os.environ["WG_TEST_APPLY_DIR"]
            result = await wgtools.apply_server_config(None)
            self.assertEqual(
                (result.result, result.mode, result.peer_count),
                ("applied", "systemd", 0),
            )
            self.assertIn("PostUp = echo ready", apply.await_args.args[1])
            apply.side_effect = RuntimeError("service failed")
            with self.assertRaises(HTTPException) as error:
                await wgtools.apply_server_config(None)
            self.assertEqual(error.exception.status_code, 503)

    async def test_test_container_mode_remains_available(self):
        """Test mode never calls systemd and omits server hooks."""
        server = {
            **generate_keypair(),
            "ServerInterface": "wg0",
            "Address": "10.0.0.1/24",
            "ListenPort": 51820,
            "PostUpScript": "echo ready",
        }
        with tempfile.TemporaryDirectory() as directory:
            with (
                patch.dict(os.environ, {"WG_TEST_APPLY_DIR": directory}),
                patch.object(
                    wgtools, "get_wireguard_data", AsyncMock(return_value=server)
                ),
                patch.object(
                    wgtools, "get_all_client_data", AsyncMock(return_value=[])
                ),
                patch.object(wgtools, "apply_systemd_config", AsyncMock()) as systemd,
                patch.object(
                    wgtools, "apply_test_container_config", AsyncMock()
                ) as apply,
            ):
                result = await wgtools.apply_server_config(None)
                self.assertEqual(result.mode, "test-container")
                self.assertNotIn("PostUp", apply.await_args.args[2])
                systemd.assert_not_awaited()

    async def test_email_and_download_include_routing_directives_only_in_config(self):
        """The QR omits Linux routing directives while both files retain them."""
        client = {
            **generate_keypair(),
            "Email": "client@example.com",
            "IPAllocation": "10.0.0.13/32",
            "AllowedIPs": "10.0.0.0/24",
            "UseDNS": True,
            "PresharedKey": generate_keypair()["PrivateKey"],
        }
        server = generate_keypair()
        global_settings = {
            "Endpoint": "vpn.example.com:51820",
            "MTU": 1500,
            "DNSServer": "10.0.0.1",
            "PersistentKeepalive": 25,
            "FirewallMark": "0xca6c",
            "Table": "auto",
        }
        config = generate_client_config(client, server, global_settings)
        self.assertIn("FwMark = 0xca6c\n", config)
        self.assertIn("Table = auto\n", config)
        qr_config = config.replace("FwMark = 0xca6c\n", "").replace(
            "Table = auto\n", ""
        )

        async def lookup(db, entry_type, name):
            return {"client": client, "server": server, "global": global_settings}[
                name if entry_type == "config" else entry_type
            ]

        with (
            patch.object(wgtools, "get_wireguard_data", AsyncMock(side_effect=lookup)),
            patch.object(wgtools, "send_email", AsyncMock()) as send,
        ):
            download = await wgtools.download_client_config("client", None)
            self.assertEqual(download.body, config.encode())
            result = await wgtools.email_client_config("client", None)
            self.assertEqual(result.result, "success")
            args = send.await_args
            message = MessageSchema(
                subject=args.args[1],
                recipients=args.args[0],
                body=args.args[2],
                subtype=MessageType.plain,
                attachments=args.kwargs["attachments"],
            )
            mime = await MailMsg(message)._message("test@example.com")
            parts = {
                part.get_filename(): part for part in mime.walk() if part.get_filename()
            }
            self.assertEqual(
                set(parts), {"wireguard-client.conf", "wireguard-client-qr.png"}
            )
            self.assertEqual(
                parts["wireguard-client.conf"].get_payload(decode=True), config.encode()
            )
            self.assertEqual(
                parts["wireguard-client-qr.png"].get_content_type(), "image/png"
            )
            image = Image.open(
                BytesIO(parts["wireguard-client-qr.png"].get_payload(decode=True))
            )
            expected = make(qr_config).get_image()
            self.assertIsNone(
                ImageChops.difference(
                    image.convert("RGB"), expected.convert("RGB")
                ).getbbox()
            )

    async def test_email_qr_keeps_config_without_routing_directives(self):
        """A config without Linux routing directives is encoded unchanged."""
        config = "[Interface]\nPrivateKey = example\n\n[Peer]\nPublicKey = example\n"
        with (
            patch.object(
                wgtools,
                "get_client_config",
                AsyncMock(return_value=({"Email": "client@example.com"}, config)),
            ),
            patch.object(wgtools, "create_qr_attachment") as qr,
            patch.object(wgtools, "send_email", AsyncMock()),
        ):
            await wgtools.email_client_config("client", None)
            qr.assert_called_once_with("wireguard-client-qr.png", config)

    async def test_qr_overflow_does_not_send_email(self):
        """An oversized QR payload produces an error without sending a partial email."""
        with (
            patch.object(
                wgtools,
                "get_client_config",
                AsyncMock(return_value=({"Email": "client@example.com"}, "config")),
            ),
            patch.object(
                wgtools, "create_qr_attachment", side_effect=DataOverflowError
            ),
            patch.object(wgtools, "send_email", AsyncMock()) as send,
        ):
            with self.assertRaises(HTTPException) as error:
                await wgtools.email_client_config("client", None)
            self.assertEqual(error.exception.status_code, 409)
            send.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
