import asyncio
import os
import unittest
from unittest.mock import AsyncMock, patch

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
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

from fastapi import HTTPException

from app.common.wg_status import (
    is_recent_handshake,
    parse_wireguard_dump,
    read_wireguard_status,
)
from app.routers import wgtools


class WireGuardStatusTests(unittest.IsolatedAsyncioTestCase):
    def test_parse_wireguard_dump_omits_handshake_for_never_connected_peer(self):
        """Parse peer counters and normalize peers with no handshake."""
        output = (
            "private-key public-key 51820 off\n"
            "peer-key (none) 198.51.100.2:51820 10.0.0.2/32 "
            "1700000000 2048 4096 25\n"
            "idle-key (none) (none) 10.0.0.3/32 0 0 0 off\n"
        )

        self.assertEqual(
            parse_wireguard_dump(output),
            {
                "peer-key": {
                    "Endpoint": "198.51.100.2:51820",
                    "LastHandshake": 1700000000,
                    "ReceivedBytes": 2048,
                    "TransmittedBytes": 4096,
                },
                "idle-key": {
                    "Endpoint": None,
                    "LastHandshake": None,
                    "ReceivedBytes": 0,
                    "TransmittedBytes": 0,
                },
            },
        )

    def test_parse_wireguard_dump_rejects_malformed_rows(self):
        """Reject command output that does not match the dump format."""
        with self.assertRaises(ValueError):
            parse_wireguard_dump("not-a-valid-interface-row\n")
        with self.assertRaises(ValueError):
            parse_wireguard_dump("private-key public-key 51820 off\npeer-key bad\n")

    def test_handshake_recency_window(self):
        """Mark handshakes no older than three minutes as recent."""
        self.assertTrue(is_recent_handshake(820, now=1000))
        self.assertTrue(is_recent_handshake(1000, now=1000))
        self.assertFalse(is_recent_handshake(819, now=1000))
        self.assertFalse(is_recent_handshake(1001, now=1000))
        self.assertFalse(is_recent_handshake(None, now=1000))

    async def test_reads_status_with_validated_interface(self):
        """Invoke wg with a validated interface and parse its output."""
        process = AsyncMock()
        process.communicate.return_value = (b"private public 51820 off\n", b"")
        process.returncode = 0
        with patch.object(
            asyncio, "create_subprocess_exec", AsyncMock(return_value=process)
        ) as start:
            self.assertEqual(await read_wireguard_status("wg0"), {})
        start.assert_awaited_once_with(
            "wg",
            "show",
            "wg0",
            "dump",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        start.reset_mock()
        with self.assertRaises(ValueError):
            await read_wireguard_status("../wg0")
        start.assert_not_awaited()

    async def test_connected_peer_route_combines_live_data_and_client_records(self):
        """Join live peer status to configured clients by public key."""
        server = {"ServerInterface": "wg0"}
        clients = [
            {
                "ID": "client-1",
                "Name": "Echo",
                "Email": "echo@example.com",
                "IPAllocation": "10.0.0.2/32",
                "PublicKey": "active-key",
            },
            {
                "ID": "client-2",
                "Name": "Alpha",
                "Email": "alpha@example.com",
                "IPAllocation": "10.0.0.3/32",
                "PublicKey": "idle-key",
            },
        ]
        live_peers = {
            "active-key": {
                "Endpoint": "198.51.100.2:51820",
                "LastHandshake": 1000,
                "ReceivedBytes": 2048,
                "TransmittedBytes": 4096,
            }
        }
        with (
            patch.object(wgtools, "get_wireguard_data", AsyncMock(return_value=server)),
            patch.object(
                wgtools, "get_all_client_data", AsyncMock(return_value=clients)
            ),
            patch.object(
                wgtools, "read_wireguard_status", AsyncMock(return_value=live_peers)
            ),
            patch("app.common.wg_status.time.time", return_value=1000),
        ):
            peers = await wgtools.get_connected_peers(None)

        self.assertEqual([peer.Name for peer in peers], ["Alpha", "Echo"])
        self.assertFalse(peers[0].Connected)
        self.assertEqual(peers[0].ReceivedBytes, 0)
        self.assertTrue(peers[1].Connected)
        self.assertEqual(peers[1].Endpoint, "198.51.100.2:51820")
        self.assertEqual(peers[1].PublicKey, "active-key")

    async def test_connected_peer_route_reports_missing_interface(self):
        """Return a conflict when the server interface is not configured."""
        with patch.object(wgtools, "get_wireguard_data", AsyncMock(return_value=None)):
            with self.assertRaises(HTTPException) as error:
                await wgtools.get_connected_peers(None)
        self.assertEqual(error.exception.status_code, 409)

    async def test_connected_peer_route_reports_status_command_failure(self):
        """Return a service error when runtime interface status is unavailable."""
        with (
            patch.object(
                wgtools,
                "get_wireguard_data",
                AsyncMock(return_value={"ServerInterface": "wg0"}),
            ),
            patch.object(
                wgtools,
                "read_wireguard_status",
                AsyncMock(side_effect=RuntimeError("wg unavailable")),
            ),
        ):
            with self.assertRaises(HTTPException) as error:
                await wgtools.get_connected_peers(None)
        self.assertEqual(error.exception.status_code, 503)
