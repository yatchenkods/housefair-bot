from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from src.bot.handlers.admin_handler import get_user_context
from src.bot.keyboards import (
    product_category_keyboard,
    recipe_cuisine_keyboard,
    recipe_meal_keyboard,
    recipe_time_keyboard,
    shopping_item_keyboard,
)
from src.services.cooking_service import CookingService
from src.services.perplexity_service import PerplexityService

PRODUCT_NAME, PRODUCT_QTY, PRODUCT_UNIT, PRODUCT_CAT = range(10, 14)
RECIPE_MEAL, RECIPE_CUISINE, RECIPE_TIME = range(20, 23)


def _get_cooking_service(context):
    db = context.bot_data["db"]
    perplexity = context.bot_data.get("perplexity")
    if not perplexity:
        settings = context.bot_data["settings"]
        perplexity = PerplexityService(settings.perplexity_api_key)
        context.bot_data["perplexity"] = perplexity
    return CookingService(db, perplexity)


async def addproduct_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    family, member = await get_user_context(update, context)
    if not family:
        await update.message.reply_text("Семья не найдена.")
        return ConversationHandler.END
    context.user_data["product_family"] = family
    context.user_data["product_member"] = member
    await update.message.reply_text("Введите название продукта:")
    return PRODUCT_NAME


async def product_name_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["product_name"] = update.message.text
    await update.message.reply_text("Введите количество (число):")
    return PRODUCT_QTY


async def product_qty_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        qty = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text("Введите число:")
        return PRODUCT_QTY
    context.user_data["product_qty"] = qty
    await update.message.reply_text("Введите единицу измерения (шт, кг, л, г, мл):")
    return PRODUCT_UNIT


async def product_unit_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["product_unit"] = update.message.text
    await update.message.reply_text("Выберите категорию:", reply_markup=product_category_keyboard())
    return PRODUCT_CAT


async def product_cat_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    category = query.data.split(":", 1)[1]

    service = _get_cooking_service(context)
    family = context.user_data["product_family"]
    member = context.user_data["product_member"]

    await service.add_product(
        family_id=family["id"],
        name=context.user_data["product_name"],
        quantity=context.user_data["product_qty"],
        unit=context.user_data["product_unit"],
        category=category,
        added_by=member["id"],
    )
    name = context.user_data["product_name"]
    qty = context.user_data["product_qty"]
    unit = context.user_data["product_unit"]
    await query.edit_message_text(f"Продукт добавлен: {name} ({qty} {unit}, {category})")
    return ConversationHandler.END


async def myproducts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    family, member = await get_user_context(update, context)
    if not family:
        await update.message.reply_text("Семья не найдена.")
        return

    service = _get_cooking_service(context)
    products = await service.get_products(family["id"])
    if not products:
        await update.message.reply_text("Список продуктов пуст. Добавьте: /addproduct")
        return

    by_category = {}
    for p in products:
        cat = p["category"] or "Без категории"
        by_category.setdefault(cat, []).append(p)

    lines = ["Продукты в наличии:\n"]
    for cat, items in sorted(by_category.items()):
        lines.append(f"\n{cat}:")
        for p in items:
            lines.append(f"  #{p['id']} {p['name']} - {p['quantity']} {p['unit']}")
    await update.message.reply_text("\n".join(lines))


async def removeproduct_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    family, member = await get_user_context(update, context)
    if not family:
        await update.message.reply_text("Семья не найдена.")
        return

    if not context.args:
        await update.message.reply_text("Укажите ID продукта: /removeproduct <id>")
        return

    try:
        product_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID должен быть числом.")
        return

    db = context.bot_data["db"]
    product = await db.get_product(product_id)
    if not product or product["family_id"] != family["id"]:
        await update.message.reply_text("Продукт не найден.")
        return

    service = _get_cooking_service(context)
    await service.remove_product(product_id)
    await update.message.reply_text(f"Продукт \"{product['name']}\" удален.")


async def recipe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    family, member = await get_user_context(update, context)
    if not family:
        await update.message.reply_text("Семья не найдена.")
        return ConversationHandler.END
    context.user_data["recipe_family"] = family
    context.user_data["recipe_member"] = member
    await update.message.reply_text("Какой тип блюда?", reply_markup=recipe_meal_keyboard())
    return RECIPE_MEAL


async def recipe_meal_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["recipe_meal"] = query.data.split(":", 1)[1]
    await query.edit_message_text("Какая кухня?", reply_markup=recipe_cuisine_keyboard())
    return RECIPE_CUISINE


async def recipe_cuisine_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["recipe_cuisine"] = query.data.split(":", 1)[1]
    await query.edit_message_text("Время приготовления?", reply_markup=recipe_time_keyboard())
    return RECIPE_TIME


async def recipe_time_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    cook_time = query.data.split(":", 1)[1]

    await query.edit_message_text("Генерирую рецепт...")

    service = _get_cooking_service(context)
    family = context.user_data["recipe_family"]

    recipe_text = await service.generate_recipe(
        family_id=family["id"],
        meal_type=context.user_data["recipe_meal"],
        cuisine=context.user_data["recipe_cuisine"],
        cook_time=cook_time,
    )

    context.user_data["last_recipe_text"] = recipe_text
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=recipe_text + "\n\nОтметьте приготовление: /cooked",
    )
    return ConversationHandler.END


async def suggest_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    family, member = await get_user_context(update, context)
    if not family:
        await update.message.reply_text("Семья не найдена.")
        return

    await update.message.reply_text("Подбираю рецепт...")
    service = _get_cooking_service(context)
    recipe_text = await service.generate_recipe(family["id"])
    context.user_data["last_recipe_text"] = recipe_text
    await update.message.reply_text(recipe_text + "\n\nОтметьте приготовление: /cooked")


async def cooked_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    family, member = await get_user_context(update, context)
    if not family or not member:
        await update.message.reply_text("Семья не найдена.")
        return

    recipe_text = context.user_data.get("last_recipe_text", "")
    title = recipe_text.split("\n")[0] if recipe_text else "Блюдо"

    service = _get_cooking_service(context)
    await service.save_recipe(
        family_id=family["id"],
        title=title,
        instructions=recipe_text,
        cooked_by=member["id"],
    )
    await update.message.reply_text(f"Отмечено: \"{title}\" приготовлено!")


async def shopping_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    family, member = await get_user_context(update, context)
    if not family:
        await update.message.reply_text("Семья не найдена.")
        return

    service = _get_cooking_service(context)

    if context.args:
        item = " ".join(context.args)
        await service.add_shopping_item(family["id"], item)
        await update.message.reply_text(f"\"{item}\" добавлено в список покупок.")
        return

    items = await service.get_shopping_list(family["id"])
    if not items:
        await update.message.reply_text(
            "Список покупок пуст.\nДобавьте: /shopping <название>"
        )
        return

    kb_items = [(i["id"], i["name"], bool(i["is_bought"])) for i in items]
    await update.message.reply_text(
        "Список покупок:", reply_markup=shopping_item_keyboard(kb_items)
    )


async def shopping_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data.split(":", 1)[1]

    family, _ = await get_user_context(update, context)
    if not family:
        return

    service = _get_cooking_service(context)

    if data == "done":
        await service.clear_bought_items(family["id"])
        await query.edit_message_text("Купленные товары удалены из списка.")
        return

    item_id = int(data)
    await service.toggle_shopping_item(family["id"], item_id)

    items = await service.get_shopping_list(family["id"])
    kb_items = [(i["id"], i["name"], bool(i["is_bought"])) for i in items]
    await query.edit_message_reply_markup(reply_markup=shopping_item_keyboard(kb_items))


async def cancel_cooking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END


def register_cooking_handlers(app):
    product_conv = ConversationHandler(
        entry_points=[CommandHandler("addproduct", addproduct_command)],
        states={
            PRODUCT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_name_entered)],
            PRODUCT_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_qty_entered)],
            PRODUCT_UNIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_unit_entered)],
            PRODUCT_CAT: [CallbackQueryHandler(product_cat_chosen, pattern=r"^pcat:")],
        },
        fallbacks=[CommandHandler("cancel", cancel_cooking)],
        name="addproduct_conv",
        per_chat=True,
    )

    recipe_conv = ConversationHandler(
        entry_points=[CommandHandler("recipe", recipe_command)],
        states={
            RECIPE_MEAL: [CallbackQueryHandler(recipe_meal_chosen, pattern=r"^meal:")],
            RECIPE_CUISINE: [CallbackQueryHandler(recipe_cuisine_chosen, pattern=r"^cuisine:")],
            RECIPE_TIME: [CallbackQueryHandler(recipe_time_chosen, pattern=r"^rtime:")],
        },
        fallbacks=[CommandHandler("cancel", cancel_cooking)],
        name="recipe_conv",
        per_message=True,
    )

    app.add_handler(product_conv)
    app.add_handler(recipe_conv)
    app.add_handler(CommandHandler("myproducts", myproducts_command))
    app.add_handler(CommandHandler("removeproduct", removeproduct_command))
    app.add_handler(CommandHandler("suggest", suggest_command))
    app.add_handler(CommandHandler("cooked", cooked_command))
    app.add_handler(CommandHandler("shopping", shopping_command))
    app.add_handler(CallbackQueryHandler(shopping_callback, pattern=r"^shop:"))
