import pytest

from src.database.models import Product
from src.services.cooking_service import CookingService
from src.services.perplexity_service import PerplexityService


@pytest.mark.asyncio
async def test_add_and_get_products(db, family_with_members):
    ids = family_with_members
    perplexity = PerplexityService("")
    service = CookingService(db, perplexity)

    await service.add_product(ids["family_id"], "Молоко", 1, "л", "Молочное", ids["admin_id"])
    await service.add_product(ids["family_id"], "Яйца", 10, "шт", "Другое", ids["admin_id"])

    products = await service.get_products(ids["family_id"])
    assert len(products) == 2


@pytest.mark.asyncio
async def test_remove_product(db, family_with_members):
    ids = family_with_members
    perplexity = PerplexityService("")
    service = CookingService(db, perplexity)

    await service.add_product(ids["family_id"], "Хлеб", 1, "шт", "Другое", ids["admin_id"])
    products = await service.get_products(ids["family_id"])
    assert len(products) == 1

    await service.remove_product(products[0]["id"])
    products = await service.get_products(ids["family_id"])
    assert len(products) == 0


@pytest.mark.asyncio
async def test_shopping_list(db, family_with_members):
    ids = family_with_members
    perplexity = PerplexityService("")
    service = CookingService(db, perplexity)

    await service.add_shopping_item(ids["family_id"], "Сахар")
    await service.add_shopping_item(ids["family_id"], "Соль")

    # Deduplicate
    await service.add_shopping_item(ids["family_id"], "Сахар")

    items = await service.get_shopping_list(ids["family_id"])
    assert len(items) == 2

    await service.toggle_shopping_item(ids["family_id"], items[0]["id"])
    items = await service.get_shopping_list(ids["family_id"])
    bought = [i for i in items if i["bought"]]
    assert len(bought) == 1

    await service.clear_bought_items(ids["family_id"])
    items = await service.get_shopping_list(ids["family_id"])
    assert len(items) == 1


@pytest.mark.asyncio
async def test_save_recipe(db, family_with_members):
    ids = family_with_members
    perplexity = PerplexityService("")
    service = CookingService(db, perplexity)

    recipe_id = await service.save_recipe(
        family_id=ids["family_id"],
        title="Омлет",
        instructions="Взбить яйца, пожарить.",
        cooked_by=ids["member1_id"],
    )
    assert recipe_id > 0

    recipes = await db.get_recipes_by_family(ids["family_id"])
    assert len(recipes) == 1
    assert recipes[0]["title"] == "Омлет"
