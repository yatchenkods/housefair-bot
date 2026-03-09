# housefair-bot

Telegram-бот для управления домашними делами, помощи в приготовлении еды и формирования отчетов о вкладе членов семьи.

## Возможности

- **Домашние дела**: создание, назначение (ручное/случайное/ротация), отметка выполнения, напоминания
- **Ассистент повара**: управление продуктами, генерация рецептов через Perplexity AI, список покупок
- **Отчеты**: еженедельные/ежемесячные отчеты, статистика, таблица лидеров, шуточные номинации
- **AI-помощник**: вопросы по хозяйству, советы по задачам

## Требования

- Python 3.11+
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
# Отредактируйте .env — укажите TELEGRAM_BOT_TOKEN и PERPLEXITY_API_KEY

# 3. Запуск через Docker
docker compose up -d

# Или локально:
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.main
```

## Тесты

```bash
source .venv/bin/activate
pytest tests/ -v
```

## Команды бота

### Администрирование
| Команда | Описание |
|---------|----------|
| `/start` | Приветствие |
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

## Архитектура

```
src/
├── main.py              # Точка входа
├── config.py            # Конфигурация (pydantic-settings)
├── bot/
│   ├── handlers/        # Обработчики команд
│   │   ├── admin_handler.py
│   │   ├── chores_handler.py
│   │   ├── cooking_handler.py
│   │   └── reports_handler.py
│   └── keyboards.py     # Inline-клавиатуры
├── database/
│   ├── models.py        # Pydantic-модели
│   └── repository.py    # Работа с SQLite
├── services/
│   ├── chores_service.py
│   ├── cooking_service.py
│   ├── reports_service.py
│   ├── perplexity_service.py
│   └── scheduler.py     # Напоминания и бэкапы
└── utils/
    ├── logger.py        # Loguru
    └── helpers.py       # Утилиты
```

## Стек

- Python 3.11+
- python-telegram-bot 21.x
- SQLite + aiosqlite (WAL mode)
- Perplexity AI (через OpenAI SDK)
- Docker + Docker Compose
- loguru, pydantic, pytest
