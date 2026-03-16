from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Protocol
from zoneinfo import ZoneInfo

from kiteconnect import KiteConnect

from app.core.secrets import SecretBox, SecretsError, mask_secret
from app.core.settings import Settings
from app.models.orm import BrokerConnectionStatus, BrokerName
from app.services.repos.broker_connections import BrokerConnectionRepository


class KiteProfileClient(Protocol):
    def profile(self) -> dict[str, Any]: ...


def _utcnow() -> datetime:
    return datetime.now(tz=ZoneInfo("UTC"))


def _default_kite_client_factory(api_key: str, access_token: str) -> KiteProfileClient:
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)
    return kite


@dataclass(frozen=True)
class KiteBrokerSettingsService:
    """DB-backed broker settings for Zerodha/Kite.

    Responsibilities:
    - store credentials encrypted-at-rest (requires SIGMALAB_ENCRYPTION_KEY)
    - provide a masked/public view for UI
    - test connectivity safely via profile call
    """

    repo: BrokerConnectionRepository
    settings: Settings
    kite_client_factory: Callable[[str, str], KiteProfileClient] = _default_kite_client_factory

    def get_public_state(self) -> dict[str, Any]:
        row = self.repo.get_by_name(BrokerName.ZERODHA_KITE)
        if row is None:
            return {
                "broker_name": BrokerName.ZERODHA_KITE.value,
                "configured": False,
                "status": BrokerConnectionStatus.DISCONNECTED.value,
                "masked": {},
                "metadata": {},
                "last_verified_at": None,
            }
        meta = dict(row.config_metadata or {})
        masked = meta.get("masked") or {}
        return {
            "broker_name": row.broker_name.value,
            "configured": bool(meta.get("configured")),
            "status": row.status.value,
            "masked": masked,
            "metadata": {k: v for k, v in meta.items() if k != "masked"},
            "last_verified_at": row.last_verified_at.isoformat() if row.last_verified_at else None,
        }

    def save_credentials(
        self,
        *,
        api_key: str | None,
        api_secret: str | None,
        access_token: str | None,
    ) -> dict[str, Any]:
        row = self.repo.get_or_create(BrokerName.ZERODHA_KITE)

        # Load and merge existing encrypted secrets (if present).
        secrets = dict(row.encrypted_secrets or {})
        if api_key is not None:
            secrets["api_key"] = api_key
        if api_secret is not None:
            secrets["api_secret"] = api_secret
        if access_token is not None:
            secrets["access_token"] = access_token

        # Encrypt-at-rest.
        box = SecretBox.from_key(self.settings.encryption_key)
        row.encrypted_secrets = box.encrypt_mapping(secrets)

        masked = {
            "api_key": mask_secret(secrets.get("api_key")),
            "api_secret": mask_secret(secrets.get("api_secret")),
            "access_token": mask_secret(secrets.get("access_token")),
        }
        row.config_metadata = {
            **(row.config_metadata or {}),
            "configured": bool(secrets.get("api_key") and secrets.get("api_secret")),
            "has_access_token": bool(secrets.get("access_token")),
            "masked": masked,
            # Reset last test status when creds change.
            "last_test_status": None,
            "last_test_message": None,
            "profile": (row.config_metadata or {}).get("profile"),
        }

        # Saving creds does not imply connectivity until tested.
        row.status = BrokerConnectionStatus.DISCONNECTED
        self.repo.update(row)
        return self.get_public_state()

    def clear_session(self) -> dict[str, Any]:
        row = self.repo.get_or_create(BrokerName.ZERODHA_KITE)
        meta = dict(row.config_metadata or {})
        masked = dict((meta.get("masked") or {}))

        if row.encrypted_secrets:
            # Keep api_key/api_secret, drop access_token.
            box = SecretBox.from_key(self.settings.encryption_key)
            dec = box.decrypt_mapping(row.encrypted_secrets)
            dec["access_token"] = None
            row.encrypted_secrets = box.encrypt_mapping(dec)
            masked["access_token"] = None

        row.config_metadata = {
            **meta,
            "has_access_token": False,
            "masked": masked,
            "last_test_status": None,
            "last_test_message": None,
        }
        row.status = BrokerConnectionStatus.DISCONNECTED
        self.repo.update(row)
        return self.get_public_state()

    def test_connection(self) -> dict[str, Any]:
        row = self.repo.get_or_create(BrokerName.ZERODHA_KITE)

        if not row.encrypted_secrets:
            raise ValueError("Kite is not configured. Save credentials first.")

        box = SecretBox.from_key(self.settings.encryption_key)
        dec = box.decrypt_mapping(row.encrypted_secrets)
        api_key = dec.get("api_key")
        access_token = dec.get("access_token")
        if not api_key or not access_token:
            raise ValueError("Kite requires api_key and access_token to test connectivity.")

        try:
            client = self.kite_client_factory(str(api_key), str(access_token))
            profile = client.profile() or {}
            # Store a conservative snapshot only.
            safe_profile = {
                "user_id": profile.get("user_id"),
                "user_name": profile.get("user_name"),
                "user_type": profile.get("user_type"),
                "email": profile.get("email"),
                "broker": "zerodha_kite",
            }
            row.config_metadata = {
                **(row.config_metadata or {}),
                "profile": safe_profile,
                "last_test_status": "success",
                "last_test_message": "Connection test passed.",
            }
            row.status = BrokerConnectionStatus.CONNECTED
            row.last_verified_at = _utcnow()
            self.repo.update(row)
            return {
                "status": "ok",
                "tested_at": row.last_verified_at.isoformat(),
                "message": "Connection test passed.",
                "profile": safe_profile,
            }
        except SecretsError:
            raise
        except Exception as e:
            # Keep diagnostics user-safe.
            msg = str(e)
            row.config_metadata = {
                **(row.config_metadata or {}),
                "last_test_status": "failed",
                "last_test_message": msg[:500],
            }
            row.status = BrokerConnectionStatus.ERROR
            row.last_verified_at = _utcnow()
            self.repo.update(row)
            return {
                "status": "error",
                "tested_at": row.last_verified_at.isoformat(),
                "message": msg[:500],
            }

