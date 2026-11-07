import asyncio
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-with-at-least-32-bytes")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("DOMAIN", "example.com")
os.environ.setdefault("MAIL_FROM", "test@example.com")
os.environ.setdefault("MAIL_PORT", "1025")
os.environ.setdefault("MAIL_SERVER", "localhost")
os.environ.setdefault("MAIL_STARTTLS", "false")
os.environ.setdefault("MAIL_SSL_TLS", "false")
os.environ.setdefault("USE_CREDENTIALS", "false")
os.environ.setdefault("VALIDATE_CERTS", "false")

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.models import SystemUser
from app.routers import auth

TOKEN = "a" * 64


class InitialSetupTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        """Create an isolated SQLite database and API client."""
        self.directory = tempfile.TemporaryDirectory()
        self.engine = create_async_engine(
            f"sqlite+aiosqlite:///{Path(self.directory.name) / 'setup.db'}"
        )
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

        async def test_db():
            async with self.sessions() as session:
                yield session

        app = FastAPI()
        app.include_router(auth.app)
        app.dependency_overrides[get_db] = test_db
        self.client = AsyncClient(
            transport=ASGITransport(app=app), base_url="https://test"
        )
        self.token_patch = patch.dict(os.environ, {"INITIAL_SETUP_TOKEN": TOKEN})
        self.token_patch.start()
        self.payload = {
            "username": "administrator",
            "password": "a secure password",
            "setup_token": TOKEN,
        }

    async def asyncTearDown(self):
        """Close the client and delete the isolated database."""
        await self.client.aclose()
        self.token_patch.stop()
        await self.engine.dispose()
        self.directory.cleanup()

    async def test_setup_creates_admin_who_can_log_in_once(self):
        """Create an enabled administrator and prevent a second registration."""
        response = await self.client.post("/setup/initial-admin", json=self.payload)
        self.assertEqual(response.status_code, 200, response.text)
        async with self.sessions() as session:
            user = (await session.execute(select(SystemUser))).scalar_one()
            self.assertEqual((user.level, user.disabled), (3, 0))
            self.assertEqual(user.email, f"administrator@{auth.DOMAIN}")
            self.assertNotEqual(user.password, self.payload["password"])
        login = await self.client.post(
            "/session/login",
            json={"username": "administrator", "password": self.payload["password"]},
        )
        self.assertEqual(login.status_code, 204, login.text)
        for path in ("/users/me", "/users/me/"):
            current_user = await self.client.get(path, follow_redirects=False)
            self.assertEqual(current_user.status_code, 200, current_user.text)
            self.assertEqual(current_user.json()["displayname"], "administrator")
            self.assertEqual(current_user.json()["level"], 3)
        tools = await self.client.get("/users/me/tools/", follow_redirects=False)
        self.assertEqual(tools.status_code, 200, tools.text)
        self.assertIn({"UserManageTools": "/admin/users"}, tools.json()["tools"])
        second = await self.client.post("/setup/initial-admin", json=self.payload)
        self.assertEqual(second.status_code, 409)

    async def test_setup_token_is_required_and_invalid_inputs_are_rejected(self):
        """Missing or incorrect tokens and malformed input must never create users."""
        with patch.dict(os.environ, {"INITIAL_SETUP_TOKEN": ""}):
            response = await self.client.post("/setup/initial-admin", json=self.payload)
            self.assertEqual(response.status_code, 503)
        for value in ("b" * 64, "あ" * 32):
            response = await self.client.post(
                "/setup/initial-admin", json={**self.payload, "setup_token": value}
            )
            self.assertEqual(response.status_code, 403)
        for change in (
            {"username": "admin@example.com"},
            {"username": ""},
            {"password": "short"},
            {"setup_token": "short"},
        ):
            response = await self.client.post(
                "/setup/initial-admin", json={**self.payload, **change}
            )
            self.assertEqual(response.status_code, 422)
        async with self.sessions() as session:
            self.assertEqual(
                await session.scalar(select(func.count()).select_from(SystemUser)), 0
            )

    async def test_existing_disabled_user_prevents_setup(self):
        """A disabled user still means that initial setup has completed."""
        async with self.sessions() as session:
            session.add(
                SystemUser(
                    name="old",
                    email="old@example.com",
                    password="x",
                    level=1,
                    disabled=1,
                )
            )
            await session.commit()
        response = await self.client.post("/setup/initial-admin", json=self.payload)
        self.assertEqual(response.status_code, 409)

    async def test_concurrent_requests_create_only_one_admin(self):
        """Competing requests cannot both create an initial administrator."""
        with patch.object(auth, "get_password_hash", return_value="hashed"):
            responses = await asyncio.gather(
                self.client.post("/setup/initial-admin", json=self.payload),
                self.client.post(
                    "/setup/initial-admin",
                    json={**self.payload, "username": "other"},
                ),
            )
        self.assertEqual(
            sorted(response.status_code for response in responses), [200, 409]
        )
        async with self.sessions() as session:
            self.assertEqual(
                await session.scalar(select(func.count()).select_from(SystemUser)), 1
            )


if __name__ == "__main__":
    unittest.main()
