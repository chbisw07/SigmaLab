from __future__ import annotations

from kiteconnect import KiteConnect

from app.core.settings import Settings
from app.core.secrets import SecretBox
from app.models.orm import BrokerName
from app.services.repos.broker_connections import BrokerConnectionRepository


def make_kite_client(settings: Settings, session=None) -> KiteConnect:  # type: ignore[no-untyped-def]
    """Create a KiteConnect client using pre-provisioned credentials.

    PH2 non-goal: implementing the full login/request_token flow.
    """
    # Prefer DB-stored broker settings (PH7), fall back to env vars.
    if session is not None:
        row = BrokerConnectionRepository(session).get_by_name(BrokerName.ZERODHA_KITE)
        if row is not None and row.encrypted_secrets:
            dec = SecretBox.from_key(settings.encryption_key).decrypt_mapping(row.encrypted_secrets)
            api_key = dec.get("api_key")
            access_token = dec.get("access_token")
            if api_key and access_token:
                kite = KiteConnect(api_key=str(api_key))
                kite.set_access_token(str(access_token))
                return kite

    if not settings.kite_api_key:
        raise ValueError("SIGMALAB_KITE_API_KEY is required (or configure broker settings in UI)")
    if not settings.kite_access_token:
        raise ValueError("SIGMALAB_KITE_ACCESS_TOKEN is required (or configure broker settings in UI)")

    kite = KiteConnect(api_key=settings.kite_api_key)
    kite.set_access_token(settings.kite_access_token)
    return kite
