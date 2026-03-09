# housefair-bot

Telegram-бот для управления домашними делами + Telegram Mini App (WebApp) с визуальным интерфейсом.

## Возможности

- **Домашние дела**: создание, назначение (ручное/случайное/ротация), отметка выполнения, напоминания
- **Ассистент повара**: управление продуктами, генерация рецептов через Perplexity AI, список покупок
- **Отчеты**: еженедельные/ежемесячные отчеты, статистика, таблица лидеров, шуточные номинации
- **AI-помощник**: вопросы по хозяйству, советы по задачам
- **Mini App**: визуальный интерфейс прямо в Telegram — задачи, продукты, покупки, статистика

## Архитектура

```
Telegram Bot ──── WebApp кнопка (WEBAPP_URL)
                          ↓
               React App (Vite, :5173)
                  /api/* proxy
                          ↓
              FastAPI REST API (:8000)
                          ↓
                 SQLite (data/database.db)
                [shared с ботом через WAL]
```

## Требования

- Python 3.11+
- Node.js 18+ (для Mini App)
- Docker и Docker Compose (для деплоя)
- Telegram Bot Token (от @BotFather)
- Perplexity API Key (опционально)

## Быстрый старт

```bash
# 1. Клонирование
git clone git@github.com:yatchenkods/housefair-bot.git
cd housefair-bot

# 2. Настройка
cp .env.example .env
# Отредактируйте .env: TELEGRAM_BOT_TOKEN, PERPLEXITY_API_KEY, JWT_SECRET

# 3. Только бот (без Mini App)
docker compose up -d housefair-bot

# 4. Бот + API
docker compose up -d
```

### Локальная разработка с Mini App

```bash
# Установить зависимости
pip install -r requirements.txt
cd webapp && npm install && cd ..

# Запустить туннель для HTTPS (Cloudflare или ngrok)
cloudflared tunnel --url http://localhost:5173

# Запустить все процессы (бот + API + webapp)
WEBAPP_URL=https://<tunnel-url> honcho start
```

После запуска отправьте `/start` боту — появится кнопка **📱 Открыть приложение**.

## Конфигурация (.env)

| Переменная | Обязательная | Описание |
|-----------|:---:|---------|
| `TELEGRAM_BOT_TOKEN` | ✓ | Токен от @BotFather |
| `PERPLEXITY_API_KEY` | — | Для генерации рецептов |
| `DATABASE_PATH` | — | Путь к SQLite (по умолчанию `data/database.db`) |
| `JWT_SECRET` | — | Секрет для JWT токенов Mini App |
| `WEBAPP_URL` | — | HTTPS URL Mini App (ngrok/cloudflare) |
| `LOG_LEVEL` | — | `INFO` / `DEBUG` |
| `BACKUP_ENABLED` | — | Ежедневный бэкап БД (по умолчанию `true`) |
| `TZ` | — | Часовой пояс (по умолчанию `Europe/Moscow`) |

## Тесты

```bash
pytest tests/ -v
```

## Команды бота

### Администрирование
| Команда | Описание |
|---------|----------|
| `/start` | Приветствие + кнопка Mini App |
| `/help` | Справка по командам |
| `/addfamily <название>` | Создать семью |
| `/addmember @username` | Добавить участника |
| `/removemember @username` | Удалить участника |
| `/familylist` | Список семьи |
| `/settings` | Настройки |

### Домашние дела
| Команда | Описание |
|---------|----------|
| `/addchore` | Добавить задачу |
| `/mytasks` | Мои задачи |
| `/alltasks` | Все задачи семьи |
| `/done [id]` | Отметить выполнение |
| `/pending` | Невыполненные задачи |
| `/history` | История |

### Кулинария
| Команда | Описание |
|---------|----------|
| `/addproduct` | Добавить продукт |
| `/myproducts` | Список продуктов |
| `/removeproduct <id>` | Удалить продукт |
| `/recipe` | Сгенерировать рецепт |
| `/suggest` | Быстрый рецепт |
| `/cooked` | Отметить приготовление |
| `/shopping [товар]` | Список покупок |

### Отчеты
| Команда | Описание |
|---------|----------|
| `/stats` | Личная статистика |
| `/familystats` | Статистика семьи |
| `/weekreport` | Отчет за неделю |
| `/monthreport` | Отчет за месяц |
| `/leaderboard` | Таблица лидеров |

### AI-помощник
| Команда | Описание |
|---------|----------|
| `/ai <вопрос>` | Задать вопрос |
| `/improve <задача>` | Совет по задаче |

## REST API

FastAPI сервер на порту `8000`. Документация: `http://localhost:8000/docs`

| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/auth/validate` | Telegram initData → JWT |
| `GET` | `/dashboard` | Сводная статистика |
| `GET/POST` | `/chores` | Задачи |
| `PATCH` | `/chores/{id}/done` | Отметить выполненной |
| `DELETE` | `/chores/{id}` | Удалить задачу |
| `GET/POST` | `/products` | Продукты |
| `DELETE` | `/products/{id}` | Удалить продукт |
| `GET/POST` | `/shopping` | Список покупок |
| `PATCH` | `/shopping/{id}` | Переключить is_bought |
| `DELETE` | `/shopping/bought` | Очистить купленные |
| `GET` | `/stats?period=week\|month` | Статистика |
| `GET` | `/health` | Проверка состояния |

## Структура проекта

```
src/
├── main.py              # Точка входа бота
├── config.py            # Конфигурация (pydantic-settings)
├── api/                 # FastAPI REST API
│   ├── main.py          # Приложение + lifespan
│   ├── auth.py          # HMAC-SHA256 валидация + JWT
│   ├── deps.py          # FastAPI зависимости
│   └── routers/         # Роуты по доменам
├── bot/
│   ├── handlers/        # Обработчики команд Telegram
│   └── keyboards.py     # Клавиатуры (inline + webapp)
├── database/
│   ├── models.py        # Pydantic-модели
│   └── repository.py    # Работа с SQLite (aiosqlite)
├── services/            # Бизнес-логика
└── utils/               # Логгер, хелперы

webapp/                  # React Mini App
├── src/
│   ├── api/client.ts    # Axios + JWT interceptor
│   ├── hooks/           # useTelegram, useAuth
│   ├── pages/           # Dashboard, Chores, Products, Shopping, Stats
│   ├── components/      # Layout, ChoreCard, ProductCard, ShoppingItemRow
│   └── types/api.ts     # TypeScript интерфейсы
├── vite.config.ts       # Vite + proxy /api → :8000
└── package.json
```

## Стек

**Backend:**
- Python 3.11+, python-telegram-bot 21.x
- FastAPI + uvicorn, python-jose (JWT)
- SQLite + aiosqlite (WAL mode, busy_timeout=5000)
- Perplexity AI (через OpenAI SDK)
- loguru, pydantic, pytest

**Frontend:**
- React 18 + TypeScript + Vite
- @telegram-apps/sdk (WebApp initData, тема)
- react-router-dom v6, axios, recharts

**Инфраструктура:**
- Docker + Docker Compose
- honcho (Procfile для dev)
- cloudflared / ngrok (HTTPS туннель для WebApp)
