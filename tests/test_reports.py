import pytest

from src.services.chores_service import ChoresService
from src.services.cooking_service import CookingService
from src.services.perplexity_service import PerplexityService
from src.services.reports_service import ReportsService


@pytest.mark.asyncio
async def test_calculate_stats(db, family_with_members):
    ids = family_with_members
    chores_service = ChoresService(db)
    perplexity = PerplexityService("")
    reports_service = ReportsService(db, perplexity)

    # Create and complete chores
    for i in range(3):
        cid = await chores_service.create_chore(ids["family_id"], f"Task {i}", ids["admin_id"])
        await chores_service.assign_chore(cid, ids["family_id"], mode="manual", member_id=ids["admin_id"])
        await chores_service.complete_chore(cid)

    for i in range(2):
        cid = await chores_service.create_chore(ids["family_id"], f"Task M{i}", ids["member1_id"])
        await chores_service.assign_chore(cid, ids["family_id"], mode="manual", member_id=ids["member1_id"])
        await chores_service.complete_chore(cid)

    stats = await reports_service.calculate_stats(ids["family_id"], "2000-01-01")
    assert stats["total"] == 5
    assert stats["members"]["Admin"]["chores"] == 3
    assert stats["members"]["Member 1"]["chores"] == 2


@pytest.mark.asyncio
async def test_weekly_report_format(db, family_with_members):
    ids = family_with_members
    perplexity = PerplexityService("")
    reports_service = ReportsService(db, perplexity)

    text = await reports_service.format_weekly_report(ids["family_id"])
    assert "Отчет за неделю" in text


@pytest.mark.asyncio
async def test_personal_stats(db, family_with_members):
    ids = family_with_members
    perplexity = PerplexityService("")
    reports_service = ReportsService(db, perplexity)

    text = await reports_service.format_personal_stats(
        ids["family_id"], ids["admin_id"], "Admin"
    )
    assert "Статистика Admin" in text


@pytest.mark.asyncio
async def test_leaderboard(db, family_with_members):
    ids = family_with_members
    perplexity = PerplexityService("")
    reports_service = ReportsService(db, perplexity)

    text = await reports_service.build_leaderboard(ids["family_id"])
    assert "Таблица лидеров" in text


@pytest.mark.asyncio
async def test_nominations_fallback(db, family_with_members):
    ids = family_with_members
    perplexity = PerplexityService("")  # No API key = fallback

    stats = {
        "members": {
            "Admin": {"chores": 5, "recipes": 2},
            "Member 1": {"chores": 3, "recipes": 1},
        }
    }
    result = await perplexity.generate_nominations(stats)
    assert "Золотая швабра" in result
