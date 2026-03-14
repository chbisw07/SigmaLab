from __future__ import annotations

import argparse
import os
import sys

from kiteconnect import KiteConnect


def _get_env(name: str) -> str | None:
    v = os.environ.get(name)
    return v.strip() if v else None


def cmd_login_url(api_key: str) -> int:
    kite = KiteConnect(api_key=api_key)
    print(kite.login_url())
    return 0


def cmd_exchange(api_key: str, api_secret: str, request_token: str) -> int:
    kite = KiteConnect(api_key=api_key)
    data = kite.generate_session(request_token, api_secret=api_secret)
    access_token = data.get("access_token")
    if not access_token:
        print("ERROR: access_token missing from generate_session response", file=sys.stderr)
        return 2

    # Print in a copy/paste-friendly form for .env
    print(f"SIGMALAB_KITE_ACCESS_TOKEN={access_token}")
    return 0


def main(argv: list[str] | None = None) -> int:
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
        return cmd_exchange(args.api_key, args.api_secret, args.request_token)

    return 2


if __name__ == "__main__":
    raise SystemExit(main())

