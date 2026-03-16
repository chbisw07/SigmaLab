from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from cryptography.fernet import Fernet

from app.core.secrets import SecretsError
from app.core.settings import Settings
from app.models.orm import BrokerConnection, BrokerConnectionStatus, BrokerName
from app.services.broker_settings import KiteBrokerSettingsService


@dataclass
class _FakeRepo:
    row: BrokerConnection | None = None

    def get_by_name(self, broker_name: BrokerName) -> BrokerConnection | None:  # noqa: ARG002
        return self.row

    def get_or_create(self, broker_name: BrokerName) -> BrokerConnection:  # noqa: ARG002
        if self.row is None:
            self.row = BrokerConnection(
                broker_name=BrokerName.ZERODHA_KITE,
                status=BrokerConnectionStatus.DISCONNECTED,
                config_metadata={},
                encrypted_secrets={},
            )
        return self.row

    def update(self, row: BrokerConnection) -> BrokerConnection:
        self.row = row
        return row


class _FakeKiteOk:
    def profile(self) -> dict[str, Any]:
        return {
            "user_id": "AB1234",
            "user_name": "Test User",
            "user_type": "individual",
            "email": "test@example.com",
        }


class _FakeKiteFail:
    def profile(self) -> dict[str, Any]:
        raise RuntimeError("auth failed: invalid token")


class _FakeKiteConnect:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self._access_token: str | None = None

    def login_url(self) -> str:
        return f"https://kite.zerodha.com/connect/login?api_key={self.api_key}&v=3"

    def generate_session(self, request_token: str, api_secret: str) -> dict[str, Any]:  # noqa: ARG002
        if request_token != "rt_ok":
            raise RuntimeError("Token is invalid or has expired.")
        return {"access_token": "at_ok"}

    def set_access_token(self, access_token: str) -> None:
        self._access_token = access_token


def test_save_credentials_requires_encryption_key() -> None:
    repo = _FakeRepo()
    svc = KiteBrokerSettingsService(repo=repo, settings=Settings(env="test", encryption_key=None))
    with pytest.raises(SecretsError, match="ENCRYPTION_KEY"):
        svc.save_credentials(api_key="k", api_secret="s", access_token="t")


def test_save_and_public_state_masks_secrets() -> None:
    key = Fernet.generate_key().decode("utf-8")
    repo = _FakeRepo()
    svc = KiteBrokerSettingsService(repo=repo, settings=Settings(env="test", encryption_key=key))

    state = svc.save_credentials(api_key="api_key_1234", api_secret="api_secret_9999", access_token="access_token_5555")
    assert state["configured"] is True
    assert state["masked"]["api_key"].endswith("1234")
    assert "api_key_1234" not in str(state)
    assert "api_secret_9999" not in str(state)
    assert "access_token_5555" not in str(state)

    state2 = svc.get_public_state()
    assert state2["masked"]["api_key"].endswith("1234")
    assert "api_key_1234" not in str(state2)


def test_clear_session_drops_access_token_only() -> None:
    key = Fernet.generate_key().decode("utf-8")
    repo = _FakeRepo()
    svc = KiteBrokerSettingsService(repo=repo, settings=Settings(env="test", encryption_key=key))
    svc.save_credentials(api_key="k", api_secret="s", access_token="t")

    state = svc.clear_session()
    assert state["configured"] is True
    assert state["metadata"]["has_access_token"] is False
    assert state["masked"]["access_token"] is None


def test_test_connection_success_updates_status_and_profile() -> None:
    key = Fernet.generate_key().decode("utf-8")
    repo = _FakeRepo()
    svc = KiteBrokerSettingsService(
        repo=repo,
        settings=Settings(env="test", encryption_key=key),
        kite_client_factory=lambda api_key, access_token: _FakeKiteOk(),  # noqa: ARG005
    )
    svc.save_credentials(api_key="k", api_secret="s", access_token="t")

    resp = svc.test_connection()
    assert resp["status"] == "ok"
    assert repo.row is not None
    assert repo.row.status == BrokerConnectionStatus.CONNECTED
    public = svc.get_public_state()
    assert public["metadata"]["last_test_status"] == "success"
    assert public["metadata"]["profile"]["user_id"] == "AB1234"


def test_test_connection_failure_is_user_safe_and_does_not_leak_secrets() -> None:
    key = Fernet.generate_key().decode("utf-8")
    repo = _FakeRepo()
    svc = KiteBrokerSettingsService(
        repo=repo,
        settings=Settings(env="test", encryption_key=key),
        kite_client_factory=lambda api_key, access_token: _FakeKiteFail(),  # noqa: ARG005
    )
    svc.save_credentials(api_key="k1234", api_secret="s9999", access_token="t5555")

    resp = svc.test_connection()
    assert resp["status"] == "error"
    assert "invalid token" in resp["message"]
    assert "k1234" not in str(resp)
    assert "s9999" not in str(resp)
    assert "t5555" not in str(resp)


def test_login_url_requires_configured_api_key() -> None:
    key = Fernet.generate_key().decode("utf-8")
    repo = _FakeRepo()
    svc = KiteBrokerSettingsService(repo=repo, settings=Settings(env="test", encryption_key=key))
    with pytest.raises(ValueError, match="not configured"):
        svc.login_url()


def test_login_url_returns_url() -> None:
    key = Fernet.generate_key().decode("utf-8")
    repo = _FakeRepo()
    svc = KiteBrokerSettingsService(
        repo=repo,
        settings=Settings(env="test", encryption_key=key),
        kite_connect_factory=lambda api_key: _FakeKiteConnect(api_key),
    )
    svc.save_credentials(api_key="k", api_secret="s", access_token=None)
    r = svc.login_url()
    assert r["status"] == "ok"
    assert "api_key=k" in r["login_url"]


def test_exchange_request_token_persists_access_token() -> None:
    key = Fernet.generate_key().decode("utf-8")
    repo = _FakeRepo()
    svc = KiteBrokerSettingsService(
        repo=repo,
        settings=Settings(env="test", encryption_key=key),
        kite_connect_factory=lambda api_key: _FakeKiteConnect(api_key),
        kite_client_factory=lambda api_key, access_token: _FakeKiteOk(),  # noqa: ARG005
    )
    svc.save_credentials(api_key="k", api_secret="s", access_token=None)
    resp = svc.exchange_request_token(request_token="rt_ok")
    assert resp["status"] == "ok"
    state = svc.get_public_state()
    assert state["metadata"]["has_access_token"] is True
    assert state["status"] == "connected"


def test_force_reset_wipes_secrets() -> None:
    key = Fernet.generate_key().decode("utf-8")
    repo = _FakeRepo()
    svc = KiteBrokerSettingsService(repo=repo, settings=Settings(env="test", encryption_key=key))
    svc.save_credentials(api_key="k", api_secret="s", access_token="t")
    s = svc.force_reset()
    assert s["configured"] is False
