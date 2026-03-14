from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from kiteconnect import KiteConnect


def _load_dotenv() -> None:
    """Load repo `.env` into the process env for local convenience."""
    try:
        from dotenv import load_dotenv  # type: ignore[import-not-found]
    except Exception:
        return

    repo_root = Path(__file__).resolve().parents[1]
    env_path = repo_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)


def _get_env(name: str) -> str | None:
    v = os.environ.get(name)
    return v.strip() if v else None


def cmd_login_url(api_key: str) -> int:
    kite = KiteConnect(api_key=api_key)
    print(kite.login_url())
    return 0


def _extract_request_token(value: str) -> str:
    v = value.strip()
    if not v:
        raise ValueError("request_token is required")

    # Allow passing the full redirect URL (it contains ?request_token=...).
    if v.startswith("http://") or v.startswith("https://"):
        q = parse_qs(urlparse(v).query)
        token = (q.get("request_token") or [None])[0]
        if token:
            return token
        raise ValueError(
            "No request_token found in the provided URL. "
            "Paste the *redirect URL after login* (it contains request_token=...), "
            "not the Kite login URL."
        )

    # Otherwise assume it's already a request_token string.
    return v


def cmd_exchange(api_key: str, api_secret: str, request_token: str) -> int:
    kite = KiteConnect(api_key=api_key)
    token = _extract_request_token(request_token)
    data = kite.generate_session(token, api_secret=api_secret)
    access_token = data.get("access_token")
    if not access_token:
        print("ERROR: access_token missing from generate_session response", file=sys.stderr)
        return 2

    # Print in a copy/paste-friendly form for .env
    print(f"SIGMALAB_KITE_ACCESS_TOKEN={access_token}")
    return 0


def main(argv: list[str] | None = None) -> int:
    _load_dotenv()

    p = argparse.ArgumentParser(
        description="Helper to get a Zerodha KiteConnect access_token for SigmaLab (.env)."
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    p_url = sub.add_parser("login-url", help="Print the Kite login URL to open in a browser.")
    p_url.add_argument("--api-key", default=_get_env("SIGMALAB_KITE_API_KEY") or "")

    p_x = sub.add_parser("exchange", help="Exchange request_token for access_token.")
    p_x.add_argument("--api-key", default=_get_env("SIGMALAB_KITE_API_KEY") or "")
    p_x.add_argument("--api-secret", default=_get_env("SIGMALAB_KITE_API_SECRET") or "")
    p_x.add_argument("--request-token", required=True)

    args = p.parse_args(argv)

    if args.cmd == "login-url":
        if not args.api_key:
            p_url.error("--api-key or SIGMALAB_KITE_API_KEY is required")
        return cmd_login_url(args.api_key)

    if args.cmd == "exchange":
        if not args.api_key:
            p_x.error("--api-key or SIGMALAB_KITE_API_KEY is required")
        if not args.api_secret:
            p_x.error("--api-secret or SIGMALAB_KITE_API_SECRET is required")
        try:
            return cmd_exchange(args.api_key, args.api_secret, args.request_token)
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            print(
                "Hint: run `login-url`, open it, login, then paste the redirect URL or the request_token value.",
                file=sys.stderr,
            )
            return 2

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
