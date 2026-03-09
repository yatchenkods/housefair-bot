# HouseFair Bot

Telegram-бот для управления домашними делами в семье.

## Архитектура

```
Telegram Bot (python-telegram-bot 21.x)
    ↓ HTTP/REST
FastAPI Backend (единственный компонент с доступом к БД)
    ↓ ORM (SQLModel/SQLAlchemy)
SQLite (WAL mode) → PostgreSQL (будущее, только изменение DATABASE_URL)
```

## Быстрый старт

### 1. Настройка переменных окружения

```bash
cp .env.example .env
# Отредактируйте .env: укажите TELEGRAM_TOKEN
```

### 2. Запуск через Docker Compose

```bash
docker-compose up -d
```

### 3. Просмотр логов

```bash
docker-compose logs -f
```

### 4. Остановка

```bash
docker-compose down
```

## Переменные окружения

See `.env.example`:

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `TELEGRAM_TOKEN` | Токен Telegram-бота (обязательно) | — |
| `API_BASE_URL` | URL FastAPI бэкенда | `http://localhost:8000` |
| `DATABASE_URL` | URL SQLite/PostgreSQL | `sqlite:///./data/database.db` |
| `JWT_SECRET` | Секрет JWT | `change_me_in_production` |

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Регистрация / начало работы |
| `/addchore`, `/task` | Добавить задачу |
| `/mytasks` | Мои задачи |
| `/alltasks` | Все задачи семьи |
| `/pending` | Невыполненные задачи |
| `/history` | История выполненных |
| `/done <id>` | Отметить задачу выполненной |

## API эндпоинты

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/families` | Создать семью |
| GET | `/api/families` | Список семей |
| GET | `/api/families/{chat_id}` | Семья по chat_id |
| POST | `/api/members` | Добавить участника |
| GET | `/api/members` | Список участников |
| GET | `/api/members/by_user` | Участник по user_id |
| POST | `/api/chores` | Создать задачу |
| GET | `/api/chores` | Список задач |
| PATCH | `/api/chores/{id}` | Обновить задачу |
| POST | `/api/chores/{id}/assign` | Назначить задачу |
| POST | `/api/chores/{id}/complete` | Отметить выполненной |
| GET | `/api/chores/history` | История выполненных |

## Разработка

```bash
# Создать venv и установить зависимости
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Запустить тесты
pytest tests/ -v

# Запустить API локально
uvicorn src.api.main:app --reload --port 8000
```
