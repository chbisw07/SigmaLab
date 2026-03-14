from __future__ import annotations

from kiteconnect import KiteConnect

from app.core.settings import Settings


def make_kite_client(settings: Settings) -> KiteConnect:
    """Create a KiteConnect client using pre-provisioned credentials.

    PH2 non-goal: implementing the full login/request_token flow.
    """
    if not settings.kite_api_key:
        raise ValueError("SIGMALAB_KITE_API_KEY is required to create a Kite client")
    if not settings.kite_access_token:
        raise ValueError("SIGMALAB_KITE_ACCESS_TOKEN is required to create a Kite client")

    kite = KiteConnect(api_key=settings.kite_api_key)
    kite.set_access_token(settings.kite_access_token)
    return kite

