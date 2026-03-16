# How To Generate `SIGMALAB_KITE_ACCESS_TOKEN` (Zerodha/Kite)

SigmaLab does not implement the full Kite login flow. Instead, use the helper script to generate an access token and then paste it into your backend `.env` or into the PH7 Settings UI (stored encrypted-at-rest in PostgreSQL).

## Step 1: Get Login URL

```bash
python scripts/kite_access_token_helper.py login-url
```

This prints a URL like:

```text
https://kite.zerodha.com/connect/login?api_key=<YOUR_API_KEY>&v=3
```

Open it in your browser, complete the login, and you will be redirected to a URL containing a `request_token`, like:

```text
http://localhost:8000/kite/callback?...&request_token=<REQUEST_TOKEN>
```

## Step 2: Exchange Request Token For Access Token

```bash
python scripts/kite_access_token_helper.py exchange --request-token "<REQUEST_TOKEN>"
```

This prints:

```text
SIGMALAB_KITE_ACCESS_TOKEN=<ACCESS_TOKEN>
```

## Step 3: Save It

Option A: Put it in backend `.env`:

```text
SIGMALAB_KITE_ACCESS_TOKEN=<ACCESS_TOKEN>
```

Option B (PH7): Save it via Settings UI (encrypted-at-rest in DB). In that case, ensure:

- `SIGMALAB_ENCRYPTION_KEY` is set on the backend
- PostgreSQL is running
- migrations are applied

