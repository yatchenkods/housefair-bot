# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment

Always use the `.venv` virtual environment when working with the project:
```bash
source .venv/bin/activate
```

## Architecture

Two-service architecture. **The bot never accesses the database directly.**

```
Telegram Bot (python-telegram-bot 21.x)
    ↓ HTTP/REST
FastAPI Backend (sole DB owner)
    ↓ ORM (SQLModel/SQLAlchemy)
SQLite (MVP) → PostgreSQL (future, via DATABASE_URL change only)
```

### Services

- **Bot service** (`src/bot/`): Telegram handler logic → HTTP calls to API → formats responses. No DB connection strings, no ORM imports.
- **API backend** (`src/api/`): FastAPI, all business logic, ORM models, REST endpoints. Only component with DB access.

### Key API endpoints (from spec)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/chores` | Create chore |
| GET | `/api/chores` | List chores (filterable by family_id, assigned_to, status) |
| PATCH | `/api/chores/{id}` | Update chore (assign, etc.) |
| POST | `/api/chores/{id}/assign` | Assign chore |
| POST | `/api/chores/{id}/complete` | Mark complete |
| GET | `/api/chores/history` | Chore history |

### Data models (backend only)

- `families`: id, name, chat_id, created_at, timezone, settings (JSON)
- `members`: id, family_id, user_id, username, display_name, role (admin/member), joined_at, preferences (JSON)
- `chores`: id, family_id, title, description, chore_type (one_time/daily/weekly/monthly), category, assigned_to, created_by, created_at, due_date, completed_at, status (pending/completed/overdue), photo_url

## Common Commands

```bash
# Run API backend
uvicorn src.api.main:app --reload --port 8000

# Run bot + API together (requires Procfile)
honcho start

# Tests
pytest tests/ -v
pytest tests/test_foo.py::test_bar -v  # single test
```

## Database

- SQLite in WAL mode, stored in Docker volume at `./data:/app/data`
- Connection via `DATABASE_URL` env var (backend only)
- Daily backups to `/app/data/backups`, max 30 retained
- Switching to PostgreSQL = change `DATABASE_URL` + run migrations; bot code unchanged

## Auth

Telegram initData HMAC-SHA256 → JWT (HS256, 24h). Dev bypass: `JWT_SECRET=dev` + `user_id=0`.

## Bot Commands

`/addchore`, `/task` — create chore
`/mytasks`, `/alltasks`, `/pending`, `/history` — view chores
`/done <id>` — mark complete

Assignment modes: manual, random, rotation, free task.
