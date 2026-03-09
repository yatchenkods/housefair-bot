import pytest

from src.database.models import Chore
from src.services.chores_service import ChoresService


@pytest.mark.asyncio
async def test_create_chore(db, family_with_members):
    ids = family_with_members
    service = ChoresService(db)

    chore_id = await service.create_chore(
        family_id=ids["family_id"],
        title="Помыть посуду",
        created_by=ids["admin_id"],
        chore_type="one_time",
    )
    assert chore_id > 0

    chore = await db.get_chore(chore_id)
    assert chore["title"] == "Помыть посуду"
    assert chore["status"] == "pending"


@pytest.mark.asyncio
async def test_assign_chore_manual(db, family_with_members):
    ids = family_with_members
    service = ChoresService(db)

    chore_id = await service.create_chore(
        family_id=ids["family_id"],
        title="Вынести мусор",
        created_by=ids["admin_id"],
    )

    chore = await service.assign_chore(
        chore_id, ids["family_id"], mode="manual", member_id=ids["member1_id"]
    )
    assert chore["assigned_to"] == ids["member1_id"]


@pytest.mark.asyncio
async def test_assign_chore_random(db, family_with_members):
    ids = family_with_members
    service = ChoresService(db)

    chore_id = await service.create_chore(
        family_id=ids["family_id"],
        title="Пропылесосить",
        created_by=ids["admin_id"],
    )

    chore = await service.assign_chore(chore_id, ids["family_id"], mode="random")
    assert chore["assigned_to"] is not None


@pytest.mark.asyncio
async def test_assign_chore_rotation(db, family_with_members):
    ids = family_with_members
    service = ChoresService(db)

    chore_id = await service.create_chore(
        family_id=ids["family_id"],
        title="Полить растения",
        created_by=ids["admin_id"],
    )

    chore = await service.assign_chore(chore_id, ids["family_id"], mode="rotation")
    assert chore["assigned_to"] is not None


@pytest.mark.asyncio
async def test_complete_chore(db, family_with_members):
    ids = family_with_members
    service = ChoresService(db)

    chore_id = await service.create_chore(
        family_id=ids["family_id"],
        title="Помыть полы",
        created_by=ids["admin_id"],
    )

    chore = await service.complete_chore(chore_id)
    assert chore["status"] == "completed"
    assert chore["completed_at"] is not None


@pytest.mark.asyncio
async def test_get_pending_chores(db, family_with_members):
    ids = family_with_members
    service = ChoresService(db)

    await service.create_chore(ids["family_id"], "Задача 1", ids["admin_id"])
    await service.create_chore(ids["family_id"], "Задача 2", ids["admin_id"])

    pending = await service.get_pending(ids["family_id"])
    assert len(pending) == 2


@pytest.mark.asyncio
async def test_get_history(db, family_with_members):
    ids = family_with_members
    service = ChoresService(db)

    cid = await service.create_chore(ids["family_id"], "Выполненная", ids["admin_id"])
    await service.complete_chore(cid)

    history = await service.get_history(ids["family_id"])
    assert len(history) == 1
    assert history[0]["title"] == "Выполненная"


@pytest.mark.asyncio
async def test_recurring_chore_recreation(db, family_with_members):
    ids = family_with_members
    service = ChoresService(db)

    cid = await service.create_chore(
        ids["family_id"], "Ежедневная", ids["admin_id"], chore_type="daily"
    )
    await service.complete_chore(cid)

    count = await service.recreate_recurring()
    assert count == 1

    all_chores = await service.get_all_chores(ids["family_id"])
    pending = [c for c in all_chores if c["status"] == "pending"]
    assert len(pending) == 1
