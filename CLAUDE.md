# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment

Always use the `.venv` virtual environment when working with the project:
```bash
source .venv/bin/activate
```

Required env vars (see `.env.example`): `TELEGRAM_TOKEN`, `API_BASE_URL`, `DATABASE_URL`, `JWT_SECRET`.

## Architecture

Two-service architecture. **The bot never accesses the database directly.**

```
Telegram Bot (python-telegram-bot 21.x)
    ↓ HTTP/REST (httpx AsyncClient)
FastAPI Backend (sole DB owner)
    ↓ ORM (SQLModel/SQLAlchemy)
SQLite (MVP) → PostgreSQL (future, via DATABASE_URL change only)
```

### Services

- **API backend** (`src/api/`): FastAPI app, all business logic, ORM models, REST endpoints. Only component with DB access. Entry point: `src/api/main.py`.
- **Bot service** (`src/bot/`): Telegram handlers → calls API via `src/bot/client.py` (singleton `api: APIClient`) → formats responses for user. No DB imports allowed.
  - `src/bot/scheduler.py` — APScheduler checks overdue chores every 30 min, sends notifications via Telegram.
  - `src/bot/config.py` — pydantic-settings `BotSettings`.

### Key constraint

Bot handlers must only use `src/bot/client.APIClient` to interact with data. Never import from `src/api/` in bot code.

## Common Commands

```bash
# Run API backend (dev)
uvicorn src.api.main:app --reload --port 8000

# Run bot (dev)
python -m src.bot.main

# Run both together
honcho start

# Docker
docker-compose up -d
docker-compose logs -f

# Tests
pytest tests/ -v
pytest tests/test_chores_api.py::test_create_chore -v  # single test
```

## Testing

- pytest with `asyncio_mode = "auto"` (pyproject.toml) — async tests run without `@pytest.mark.asyncio`.
- `tests/conftest.py` provides `session` and `client` fixtures: SQLite in-memory with `StaticPool` (from `sqlalchemy.pool`) — **required** to avoid "no such table" errors. FastAPI dependency override via `app.dependency_overrides[get_session]`.
- Test files: `test_families_api.py`, `test_members_api.py`, `test_chores_api.py` — all use `TestClient` (sync).

## Database

- SQLite in WAL mode (`PRAGMA journal_mode=WAL`, `busy_timeout=5000`) — set via SQLAlchemy `connect` event in `src/api/database.py`.
- Stored at `./data/database.db` (Docker volume `./data:/app/data`).
- Daily backups to `./data/backups/`, max 30 retained (`src/api/backup.py`, APScheduler at 03:00 UTC).
- Switch to PostgreSQL = change `DATABASE_URL` only; bot code unchanged.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST/GET | `/api/families` | Create / list families |
| GET | `/api/families/{chat_id}` | Get family by Telegram chat_id |
| POST/GET | `/api/members` | Create / list members |
| GET | `/api/members/by_user` | Get member by user_id + family_id |
| POST | `/api/chores` | Create chore |
| GET | `/api/chores` | List chores (filter: family_id, assigned_to, status) |
| PATCH | `/api/chores/{id}` | Update chore |
| POST | `/api/chores/{id}/assign` | Assign chore (modes: manual, random, rotation, free) |
| POST | `/api/chores/{id}/complete` | Mark complete |
| GET | `/api/chores/history` | Chore history (filter: family_id, from_dt, to_dt) |

## Bot Commands

`/start` — register family + member, `/help` — command list
`/addchore`, `/task` — create chore (ConversationHandler)
`/mytasks`, `/alltasks`, `/pending`, `/history` — view chores
`/done <id>` — mark complete

## Build

`pyproject.toml` uses `setuptools.build_meta` as build-backend. Python >=3.11.
