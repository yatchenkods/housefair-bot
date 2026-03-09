from typing import Optional

from src.database.models import Product, Recipe
from src.database.repository import Database
from src.services.perplexity_service import PerplexityService


class CookingService:
    def __init__(self, db: Database, perplexity: PerplexityService):
        self.db = db
        self.perplexity = perplexity

    async def add_product(
        self, family_id: int, name: str, quantity: float, unit: str, category: str, added_by: int
    ) -> int:
        product = Product(
            family_id=family_id,
            name=name,
            quantity=quantity,
            unit=unit,
            category=category,
            added_by=added_by,
        )
        return await self.db.add_product(product)

    async def get_products(self, family_id: int) -> list[dict]:
        return await self.db.get_products_by_family(family_id)

    async def remove_product(self, product_id: int) -> None:
        await self.db.remove_product(product_id)

    async def generate_recipe(
        self, family_id: int, meal_type: str = "", cuisine: str = "", cook_time: str = ""
    ) -> str:
        products = await self.db.get_products_by_family(family_id)
        product_names = [f"{p['name']} ({p['quantity']} {p['unit']})" for p in products]
        if not product_names:
            product_names = ["нет продуктов в списке"]
        return await self.perplexity.generate_recipe(product_names, meal_type, cuisine, cook_time)

    async def save_recipe(
        self, family_id: int, title: str, instructions: str, cooked_by: int,
        cuisine_type: str = "", cooking_time: int = 0
    ) -> int:
        recipe = Recipe(
            family_id=family_id,
            title=title,
            instructions=instructions,
            cuisine_type=cuisine_type,
            cooking_time=cooking_time,
            cooked_by=cooked_by,
        )
        return await self.db.save_recipe(recipe)

    async def get_shopping_list(self, family_id: int) -> list[dict]:
        return await self.db.get_shopping_list(family_id)

    async def add_shopping_item(self, family_id: int, item: str) -> None:
        existing = await self.db.get_shopping_list(family_id)
        for e in existing:
            if e["name"].lower() == item.lower():
                return
        await self.db.add_shopping_item(family_id, item)

    async def toggle_shopping_item(self, family_id: int, item_id: int) -> None:
        await self.db.toggle_shopping_item(item_id)

    async def clear_bought_items(self, family_id: int) -> None:
        await self.db.clear_bought_items(family_id)
