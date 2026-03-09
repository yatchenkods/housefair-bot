from telegram import InlineKeyboardButton, InlineKeyboardMarkup

CHORE_PRESETS = [
    "Помыть посуду",
    "Вынести мусор",
    "Заказать продукты",
    "Убрать детские игрушки",
    "Погулять с питомцем",
    "Полить растения",
    "Пропылесосить",
    "Помыть полы",
    "Сменить постельное белье",
    "Почистить лоток питомца",
]


def chore_presets_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(name, callback_data=f"preset:{name}")]
        for name in CHORE_PRESETS
    ]
    buttons.append([InlineKeyboardButton("Своя задача", callback_data="preset:custom")])
    return InlineKeyboardMarkup(buttons)


def chore_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Разовая", callback_data="type:one_time")],
        [InlineKeyboardButton("Ежедневная", callback_data="type:daily")],
        [InlineKeyboardButton("Еженедельная", callback_data="type:weekly")],
        [InlineKeyboardButton("Ежемесячная", callback_data="type:monthly")],
    ])


def assign_mode_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Назначить вручную", callback_data="assign:manual")],
        [InlineKeyboardButton("Случайно", callback_data="assign:random")],
        [InlineKeyboardButton("Ротация", callback_data="assign:rotation")],
        [InlineKeyboardButton("Свободная задача", callback_data="assign:free")],
    ])


def members_keyboard(members: list[dict]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(m["display_name"], callback_data=f"member:{m['id']}")]
        for m in members
    ]
    return InlineKeyboardMarkup(buttons)


def confirm_keyboard(prefix: str = "confirm") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Да", callback_data=f"{prefix}:yes"),
            InlineKeyboardButton("Нет", callback_data=f"{prefix}:no"),
        ]
    ])


def chore_done_keyboard(chores: list[dict]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            f"#{c['id']} {c['title']}", callback_data=f"done:{c['id']}"
        )]
        for c in chores[:10]
    ]
    return InlineKeyboardMarkup(buttons)


def settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Часовой пояс", callback_data="settings:timezone")],
        [InlineKeyboardButton("Режим назначения задач", callback_data="settings:assign_mode")],
    ])


def timezone_keyboard() -> InlineKeyboardMarkup:
    tzs = [
        ("Москва (UTC+3)", "Europe/Moscow"),
        ("Калининград (UTC+2)", "Europe/Kaliningrad"),
        ("Самара (UTC+4)", "Europe/Samara"),
        ("Екатеринбург (UTC+5)", "Asia/Yekaterinburg"),
        ("Новосибирск (UTC+7)", "Asia/Novosibirsk"),
        ("Владивосток (UTC+10)", "Asia/Vladivostok"),
    ]
    buttons = [
        [InlineKeyboardButton(name, callback_data=f"tz:{tz}")]
        for name, tz in tzs
    ]
    return InlineKeyboardMarkup(buttons)


def product_category_keyboard() -> InlineKeyboardMarkup:
    categories = ["Овощи", "Фрукты", "Мясо", "Молочное", "Крупы", "Специи", "Напитки", "Другое"]
    buttons = [
        [InlineKeyboardButton(cat, callback_data=f"pcat:{cat}")]
        for cat in categories
    ]
    return InlineKeyboardMarkup(buttons)


def recipe_meal_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Завтрак", callback_data="meal:завтрак")],
        [InlineKeyboardButton("Обед", callback_data="meal:обед")],
        [InlineKeyboardButton("Ужин", callback_data="meal:ужин")],
        [InlineKeyboardButton("Десерт", callback_data="meal:десерт")],
        [InlineKeyboardButton("Перекус", callback_data="meal:перекус")],
    ])


def recipe_cuisine_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Русская", callback_data="cuisine:русская")],
        [InlineKeyboardButton("Итальянская", callback_data="cuisine:итальянская")],
        [InlineKeyboardButton("Азиатская", callback_data="cuisine:азиатская")],
        [InlineKeyboardButton("Мексиканская", callback_data="cuisine:мексиканская")],
        [InlineKeyboardButton("Любая", callback_data="cuisine:любая")],
    ])


def recipe_time_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Быстро (до 30 мин)", callback_data="rtime:быстро")],
        [InlineKeyboardButton("Средне (30-60 мин)", callback_data="rtime:средне")],
        [InlineKeyboardButton("Долго (60+ мин)", callback_data="rtime:долго")],
    ])


def shopping_item_keyboard(items: list[tuple[int, str, bool]]) -> InlineKeyboardMarkup:
    buttons = []
    for item_id, name, bought in items:
        mark = "+" if bought else " "
        buttons.append([InlineKeyboardButton(
            f"[{mark}] {name}", callback_data=f"shop:{item_id}"
        )])
    buttons.append([InlineKeyboardButton("Готово", callback_data="shop:done")])
    return InlineKeyboardMarkup(buttons)
