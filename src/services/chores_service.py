import random
from typing import Optional

from src.database.models import Chore
from src.database.repository import Database


class ChoresService:
    def __init__(self, db: Database):
        self.db = db

    async def create_chore(
        self,
        family_id: int,
        title: str,
        created_by: int,
        chore_type: str = "one_time",
        description: str = "",
        category: str = "",
    ) -> int:
        chore = Chore(
            family_id=family_id,
            title=title,
            description=description,
            chore_type=chore_type,
            category=category,
            created_by=created_by,
        )
        return await self.db.create_chore(chore)

    async def assign_chore(
        self, chore_id: int, family_id: int, mode: str = "manual", member_id: int = None
    ) -> Optional[dict]:
        members = await self.db.get_family_members(family_id)
        if not members:
            return None

        if mode == "manual" and member_id:
            target_id = member_id
        elif mode == "random":
            target = random.choice(members)
            target_id = target["id"]
        elif mode == "rotation":
            min_count = float("inf")
            target_id = members[0]["id"]
            for m in members:
                count = await self.db.get_member_chore_count_last_week(m["id"])
                if count < min_count:
                    min_count = count
                    target_id = m["id"]
        elif mode == "free":
            target_id = None
        else:
            target_id = member_id

        if target_id is not None:
            await self.db.db.execute(
                "UPDATE chores SET assigned_to = ? WHERE id = ?", (target_id, chore_id)
            )
            await self.db.db.commit()

        chore = await self.db.get_chore(chore_id)
        return chore

    async def complete_chore(self, chore_id: int) -> Optional[dict]:
        await self.db.complete_chore(chore_id)
        return await self.db.get_chore(chore_id)

    async def get_my_chores(self, member_id: int) -> list[dict]:
        return await self.db.get_chores_by_member(member_id)

    async def get_all_chores(self, family_id: int) -> list[dict]:
        return await self.db.get_chores_by_family(family_id)

    async def get_pending(self, family_id: int) -> list[dict]:
        return await self.db.get_chores_by_family(family_id, status="pending")

    async def get_history(self, family_id: int) -> list[dict]:
        return await self.db.get_chores_by_family(family_id, status="completed")

    async def recreate_recurring(self) -> int:
        completed = await self.db.get_completed_recurring_chores()
        count = 0
        for c in completed:
            new_chore = Chore(
                family_id=c["family_id"],
                title=c["title"],
                description=c["description"],
                chore_type=c["chore_type"],
                category=c["category"],
                created_by=c["created_by"],
            )
            await self.db.create_chore(new_chore)
            count += 1
        return count

    async def mark_overdue(self) -> int:
        candidates = await self.db.get_overdue_candidates()
        for c in candidates:
            await self.db.set_chore_overdue(c["id"])
        return len(candidates)
