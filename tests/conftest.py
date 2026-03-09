import pytest
import pytest_asyncio

from src.database.repository import Database


@pytest_asyncio.fixture
async def db():
    database = Database(":memory:")
    await database.connect()
    await database.init_tables()
    yield database
    await database.close()


@pytest_asyncio.fixture
async def family_with_members(db):
    family_id = await db.create_family("Test Family", 12345)
    admin_id = await db.add_member(family_id, "admin_user", "Admin", role="admin", user_id=100)
    member1_id = await db.add_member(family_id, "member1", "Member 1", role="member", user_id=101)
    member2_id = await db.add_member(family_id, "member2", "Member 2", role="member", user_id=102)
    return {
        "family_id": family_id,
        "admin_id": admin_id,
        "member1_id": member1_id,
        "member2_id": member2_id,
    }
