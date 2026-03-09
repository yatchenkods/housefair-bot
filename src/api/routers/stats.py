from datetime import datetime, timedelta

from fastapi import APIRouter, Depends

from src.api.deps import get_current_member, get_db
from src.database.repository import Database

router = APIRouter()


@router.get("")
async def get_stats(
    period: str = "week",
    member: dict = Depends(get_current_member),
    db: Database = Depends(get_db),
):
    family_id = member["family_id"]
    days = 7 if period == "week" else 30
    since = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

    chores_stats = await db.get_chores_stats(family_id, since)
    recipes_stats = await db.get_recipes_stats(family_id, since)
    popular_chores = await db.get_popular_chores(family_id, since)
    members = await db.get_family_members(family_id)

    member_map = {m["id"]: m["display_name"] for m in members}

    leaderboard = []
    chores_by_member = {r["assigned_to"]: r["count"] for r in chores_stats}
    recipes_by_member = {r["cooked_by"]: r["count"] for r in recipes_stats}
    all_member_ids = set(chores_by_member) | set(recipes_by_member)

    for mid in all_member_ids:
        chores_done = chores_by_member.get(mid, 0)
        recipes_done = recipes_by_member.get(mid, 0)
        leaderboard.append({
            "member_id": mid,
            "display_name": member_map.get(mid, f"#{mid}"),
            "chores_completed": chores_done,
            "recipes_cooked": recipes_done,
            "total_points": chores_done * 1 + recipes_done * 2,
        })

    leaderboard.sort(key=lambda x: x["total_points"], reverse=True)

    return {
        "period": period,
        "since": since,
        "leaderboard": leaderboard,
        "popular_chores": popular_chores,
    }
