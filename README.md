# SigmaLab

SigmaLab is a research and backtesting platform designed for systematic trading using Zerodha Kite data.

## Purpose

SigmaLab is a **strategy research and backtesting workbench** that complements SigmaTrader.

It is designed as a **dual-engine system**:

- Research Engine: fast watchlist-wide research (vectorized later)
- Replay / Simulation Engine: detailed trade reconstruction (event-driven later)

Important rule: strategy modules generate signals and metadata; simulation engines generate trades.

## Current Phase

PH1 – Foundation: backend scaffolding, configuration, logging, database foundation, domain model skeletons, and a small pytest suite.

## Core Features (Target)

- Watchlist-based strategy testing
- Parameter tuning
- Visual backtest charts
- Strategy comparison
- Integration with SigmaTrader

## Backend Setup (PH1)

Prereqs:

- Python 3.12+

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -e '.[dev]'
```

Environment configuration:

- Copy `.env.example` to `.env` and fill in values as needed.
- Do not commit real credentials.

Run the API (local dev):

```bash
.venv/bin/uvicorn app.main:app --reload
```

Health check:

- `GET /health`

Run tests:

```bash
.venv/bin/pytest
```

## Database & Migrations (PH1)

PostgreSQL is the intended system of record for SigmaLab. PH1 scaffolds SQLAlchemy models and Alembic.

Example Alembic commands:

```bash
.venv/bin/alembic -c backend/alembic.ini revision --autogenerate -m "init"
.venv/bin/alembic -c backend/alembic.ini upgrade head
```

Note: PH1 does not require a running PostgreSQL instance to boot the API and run tests.

## Documentation

See `/docs`
