import json
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import aiosqlite
from loguru import logger

from src.database.models import Chore, Family, Member, Product, Recipe, ShoppingItem


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.db: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        self.db = await aiosqlite.connect(self.db_path)
        self.db.row_factory = aiosqlite.Row
        await self.db.execute("PRAGMA journal_mode=WAL")
        await self.db.execute("PRAGMA foreign_keys=ON")
        await self.db.execute("PRAGMA busy_timeout=5000")
        logger.info("Database connected: {}", self.db_path)

    async def close(self) -> None:
        if self.db:
            await self.db.close()
            logger.info("Database closed")

    async def init_tables(self) -> None:
        await self.db.executescript("""
            CREATE TABLE IF NOT EXISTS families (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                chat_id INTEGER UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                timezone TEXT DEFAULT 'Europe/Moscow',
                settings TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_id INTEGER NOT NULL,
                user_id INTEGER,
                username TEXT NOT NULL,
                display_name TEXT NOT NULL,
                role TEXT DEFAULT 'member',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                preferences TEXT DEFAULT '{}',
                FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS chores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                chore_type TEXT DEFAULT 'one_time',
                category TEXT DEFAULT '',
                assigned_to INTEGER,
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                due_date TIMESTAMP,
                completed_at TIMESTAMP,
                status TEXT DEFAULT 'pending',
                photo_url TEXT DEFAULT '',
                FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                quantity REAL DEFAULT 1.0,
                unit TEXT DEFAULT 'шт',
                category TEXT DEFAULT '',
                expiry_date DATE,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                added_by INTEGER DEFAULT 0,
                FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                ingredients TEXT DEFAULT '[]',
                instructions TEXT DEFAULT '',
                cuisine_type TEXT DEFAULT '',
                cooking_time INTEGER DEFAULT 0,
                difficulty TEXT DEFAULT '',
                calories INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                cooked_by INTEGER,
                rating REAL DEFAULT 0.0,
                FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_id INTEGER NOT NULL,
                member_id INTEGER NOT NULL,
                period_type TEXT DEFAULT 'week',
                period_start DATE,
                period_end DATE,
                chores_completed INTEGER DEFAULT 0,
                recipes_cooked INTEGER DEFAULT 0,
                total_points INTEGER DEFAULT 0,
                data TEXT DEFAULT '{}',
                FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_chores_family ON chores(family_id);
            CREATE INDEX IF NOT EXISTS idx_chores_status ON chores(family_id, status);
            CREATE INDEX IF NOT EXISTS idx_chores_assigned ON chores(assigned_to, status);
            CREATE INDEX IF NOT EXISTS idx_products_family ON products(family_id);
            CREATE INDEX IF NOT EXISTS idx_members_family ON members(family_id);
            CREATE INDEX IF NOT EXISTS idx_members_user ON members(user_id);

            CREATE TABLE IF NOT EXISTS shopping_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                is_bought INTEGER DEFAULT 0,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_shopping_family ON shopping_items(family_id);
        """)
        await self.db.commit()
        await self._migrate_shopping_list()
        logger.info("Database tables initialized")

    async def check_integrity(self) -> bool:
        async with self.db.execute("PRAGMA integrity_check") as cursor:
            row = await cursor.fetchone()
            ok = row[0] == "ok"
            if not ok:
                logger.error("Database integrity check failed: {}", row[0])
            return ok

    async def backup(self, backup_dir: str, retention_days: int = 30) -> Optional[str]:
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"database_{timestamp}.db")
        try:
            shutil.copy2(self.db_path, backup_path)
            logger.info("Backup created: {}", backup_path)

            cutoff = datetime.utcnow() - timedelta(days=retention_days)
            for f in Path(backup_dir).glob("database_*.db"):
                try:
                    ts_str = f.stem.replace("database_", "")
                    ts = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
                    if ts < cutoff:
                        f.unlink()
                        logger.info("Old backup removed: {}", f)
                except ValueError:
                    pass
            return backup_path
        except Exception as e:
            logger.error("Backup failed: {}", e)
            return None

    # --- Family CRUD ---

    async def create_family(self, name: str, chat_id: int, timezone: str = "Europe/Moscow") -> int:
        async with self.db.execute(
            "INSERT INTO families (name, chat_id, timezone) VALUES (?, ?, ?)",
            (name, chat_id, timezone),
        ) as cursor:
            await self.db.commit()
            return cursor.lastrowid

    async def get_family_by_chat(self, chat_id: int) -> Optional[dict]:
        async with self.db.execute(
            "SELECT * FROM families WHERE chat_id = ?", (chat_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_family(self, family_id: int) -> Optional[dict]:
        async with self.db.execute(
            "SELECT * FROM families WHERE id = ?", (family_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def update_family_settings(self, family_id: int, settings: dict) -> None:
        await self.db.execute(
            "UPDATE families SET settings = ? WHERE id = ?",
            (json.dumps(settings, ensure_ascii=False), family_id),
        )
        await self.db.commit()

    async def update_family_timezone(self, family_id: int, timezone: str) -> None:
        await self.db.execute(
            "UPDATE families SET timezone = ? WHERE id = ?", (timezone, family_id)
        )
        await self.db.commit()

    # --- Member CRUD ---

    async def add_member(
        self, family_id: int, username: str, display_name: str, role: str = "member", user_id: int = None
    ) -> int:
        async with self.db.execute(
            "INSERT INTO members (family_id, user_id, username, display_name, role) VALUES (?, ?, ?, ?, ?)",
            (family_id, user_id, username, display_name, role),
        ) as cursor:
            await self.db.commit()
            return cursor.lastrowid

    async def get_member_by_user_id(self, user_id: int) -> Optional[dict]:
        async with self.db.execute(
            "SELECT * FROM members WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_member_by_username(self, family_id: int, username: str) -> Optional[dict]:
        async with self.db.execute(
            "SELECT * FROM members WHERE family_id = ? AND username = ?",
            (family_id, username),
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_family_members(self, family_id: int) -> list[dict]:
        async with self.db.execute(
            "SELECT * FROM members WHERE family_id = ?", (family_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def remove_member(self, member_id: int) -> None:
        await self.db.execute("DELETE FROM members WHERE id = ?", (member_id,))
        await self.db.commit()

    async def bind_member_user_id(self, member_id: int, user_id: int) -> None:
        await self.db.execute(
            "UPDATE members SET user_id = ? WHERE id = ?", (user_id, member_id)
        )
        await self.db.commit()

    # --- Chore CRUD ---

    async def create_chore(self, chore: Chore) -> int:
        async with self.db.execute(
            """INSERT INTO chores
            (family_id, title, description, chore_type, category, assigned_to, created_by, due_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                chore.family_id, chore.title, chore.description, chore.chore_type,
                chore.category, chore.assigned_to, chore.created_by,
                chore.due_date.isoformat() if chore.due_date else None, chore.status,
            ),
        ) as cursor:
            await self.db.commit()
            return cursor.lastrowid

    async def get_chore(self, chore_id: int) -> Optional[dict]:
        async with self.db.execute("SELECT * FROM chores WHERE id = ?", (chore_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_chores_by_family(self, family_id: int, status: str = None) -> list[dict]:
        if status:
            query = "SELECT * FROM chores WHERE family_id = ? AND status = ? ORDER BY created_at DESC"
            params = (family_id, status)
        else:
            query = "SELECT * FROM chores WHERE family_id = ? ORDER BY created_at DESC"
            params = (family_id,)
        async with self.db.execute(query, params) as cursor:
            return [dict(r) for r in await cursor.fetchall()]

    async def get_chores_by_member(self, member_id: int, status: str = "pending") -> list[dict]:
        async with self.db.execute(
            "SELECT * FROM chores WHERE assigned_to = ? AND status = ? ORDER BY created_at DESC",
            (member_id, status),
        ) as cursor:
            return [dict(r) for r in await cursor.fetchall()]

    async def complete_chore(self, chore_id: int) -> None:
        await self.db.execute(
            "UPDATE chores SET status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE id = ?",
            (chore_id,),
        )
        await self.db.commit()

    async def set_chore_overdue(self, chore_id: int) -> None:
        await self.db.execute(
            "UPDATE chores SET status = 'overdue' WHERE id = ?", (chore_id,)
        )
        await self.db.commit()

    async def get_overdue_candidates(self) -> list[dict]:
        async with self.db.execute(
            "SELECT * FROM chores WHERE status = 'pending' AND due_date IS NOT NULL AND due_date < datetime('now')"
        ) as cursor:
            return [dict(r) for r in await cursor.fetchall()]

    async def get_pending_chores_older_than(self, days: int) -> list[dict]:
        async with self.db.execute(
            "SELECT * FROM chores WHERE status IN ('pending', 'overdue') AND created_at < datetime('now', ?)",
            (f"-{days} days",),
        ) as cursor:
            return [dict(r) for r in await cursor.fetchall()]

    async def get_completed_recurring_chores(self) -> list[dict]:
        async with self.db.execute(
            "SELECT * FROM chores WHERE status = 'completed' AND chore_type != 'one_time'"
        ) as cursor:
            return [dict(r) for r in await cursor.fetchall()]

    async def get_member_chore_count_last_week(self, member_id: int) -> int:
        async with self.db.execute(
            "SELECT COUNT(*) FROM chores WHERE assigned_to = ? AND created_at > datetime('now', '-7 days')",
            (member_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return row[0]

    # --- Product CRUD ---

    async def add_product(self, product: Product) -> int:
        async with self.db.execute(
            "INSERT INTO products (family_id, name, quantity, unit, category, expiry_date, added_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (product.family_id, product.name, product.quantity, product.unit, product.category, product.expiry_date, product.added_by),
        ) as cursor:
            await self.db.commit()
            return cursor.lastrowid

    async def get_products_by_family(self, family_id: int) -> list[dict]:
        async with self.db.execute(
            "SELECT * FROM products WHERE family_id = ? ORDER BY category, name", (family_id,)
        ) as cursor:
            return [dict(r) for r in await cursor.fetchall()]

    async def remove_product(self, product_id: int) -> None:
        await self.db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        await self.db.commit()

    async def get_product(self, product_id: int) -> Optional[dict]:
        async with self.db.execute("SELECT * FROM products WHERE id = ?", (product_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    # --- Recipe CRUD ---

    async def save_recipe(self, recipe: Recipe) -> int:
        async with self.db.execute(
            """INSERT INTO recipes
            (family_id, title, ingredients, instructions, cuisine_type, cooking_time, difficulty, calories, cooked_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                recipe.family_id, recipe.title, recipe.ingredients, recipe.instructions,
                recipe.cuisine_type, recipe.cooking_time, recipe.difficulty,
                recipe.calories, recipe.cooked_by,
            ),
        ) as cursor:
            await self.db.commit()
            return cursor.lastrowid

    async def get_recipes_by_family(self, family_id: int, limit: int = 20) -> list[dict]:
        async with self.db.execute(
            "SELECT * FROM recipes WHERE family_id = ? ORDER BY created_at DESC LIMIT ?",
            (family_id, limit),
        ) as cursor:
            return [dict(r) for r in await cursor.fetchall()]

    async def mark_recipe_cooked(self, recipe_id: int, user_id: int) -> None:
        await self.db.execute(
            "UPDATE recipes SET cooked_by = ? WHERE id = ?", (user_id, recipe_id)
        )
        await self.db.commit()

    # --- Statistics ---

    async def get_chores_stats(self, family_id: int, since: str) -> list[dict]:
        async with self.db.execute(
            """SELECT assigned_to, COUNT(*) as count
            FROM chores
            WHERE family_id = ? AND status = 'completed' AND completed_at >= ?
            GROUP BY assigned_to""",
            (family_id, since),
        ) as cursor:
            return [dict(r) for r in await cursor.fetchall()]

    async def get_recipes_stats(self, family_id: int, since: str) -> list[dict]:
        async with self.db.execute(
            """SELECT cooked_by, COUNT(*) as count
            FROM recipes
            WHERE family_id = ? AND cooked_by IS NOT NULL AND created_at >= ?
            GROUP BY cooked_by""",
            (family_id, since),
        ) as cursor:
            return [dict(r) for r in await cursor.fetchall()]

    async def get_all_families(self) -> list[dict]:
        async with self.db.execute("SELECT * FROM families") as cursor:
            return [dict(r) for r in await cursor.fetchall()]

    async def get_popular_chores(self, family_id: int, since: str, limit: int = 5) -> list[dict]:
        async with self.db.execute(
            """SELECT title, COUNT(*) as count
            FROM chores WHERE family_id = ? AND status = 'completed' AND completed_at >= ?
            GROUP BY title ORDER BY count DESC LIMIT ?""",
            (family_id, since, limit),
        ) as cursor:
            return [dict(r) for r in await cursor.fetchall()]

    async def get_overdue_count(self, family_id: int) -> int:
        async with self.db.execute(
            "SELECT COUNT(*) FROM chores WHERE family_id = ? AND status IN ('pending', 'overdue')",
            (family_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return row[0]

    async def delete_chore(self, chore_id: int) -> None:
        await self.db.execute("DELETE FROM chores WHERE id = ?", (chore_id,))
        await self.db.commit()

    # --- Shopping Items CRUD ---

    async def add_shopping_item(self, family_id: int, name: str) -> int:
        async with self.db.execute(
            "INSERT INTO shopping_items (family_id, name) VALUES (?, ?)",
            (family_id, name),
        ) as cursor:
            await self.db.commit()
            return cursor.lastrowid

    async def get_shopping_list(self, family_id: int) -> list[dict]:
        async with self.db.execute(
            "SELECT * FROM shopping_items WHERE family_id = ? ORDER BY added_at ASC",
            (family_id,),
        ) as cursor:
            return [dict(r) for r in await cursor.fetchall()]

    async def toggle_shopping_item(self, item_id: int) -> None:
        await self.db.execute(
            "UPDATE shopping_items SET is_bought = NOT is_bought WHERE id = ?",
            (item_id,),
        )
        await self.db.commit()

    async def delete_shopping_item(self, item_id: int) -> None:
        await self.db.execute("DELETE FROM shopping_items WHERE id = ?", (item_id,))
        await self.db.commit()

    async def clear_bought_items(self, family_id: int) -> None:
        await self.db.execute(
            "DELETE FROM shopping_items WHERE family_id = ? AND is_bought = 1",
            (family_id,),
        )
        await self.db.commit()

    async def get_shopping_item(self, item_id: int) -> Optional[dict]:
        async with self.db.execute(
            "SELECT * FROM shopping_items WHERE id = ?", (item_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def _migrate_shopping_list(self) -> None:
        """Migrate shopping list from families.settings JSON to shopping_items table."""
        families = await self.get_all_families()
        for family in families:
            settings = json.loads(family.get("settings", "{}"))
            old_list = settings.get("shopping_list", [])
            if not old_list:
                continue
            # Check if already migrated (table has items for this family)
            async with self.db.execute(
                "SELECT COUNT(*) FROM shopping_items WHERE family_id = ?", (family["id"],)
            ) as cursor:
                row = await cursor.fetchone()
                if row[0] > 0:
                    continue
            for item in old_list:
                await self.db.execute(
                    "INSERT INTO shopping_items (family_id, name, is_bought) VALUES (?, ?, ?)",
                    (family["id"], item["name"], 1 if item.get("bought") else 0),
                )
            settings.pop("shopping_list", None)
            await self.db.execute(
                "UPDATE families SET settings = ? WHERE id = ?",
                (json.dumps(settings, ensure_ascii=False), family["id"]),
            )
            await self.db.commit()
            logger.info("Migrated shopping list for family {}", family["id"])
