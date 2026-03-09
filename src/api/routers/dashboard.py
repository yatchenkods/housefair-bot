from fastapi import APIRouter, Depends

from src.api.deps import get_current_member, get_db
from src.database.repository import Database

router = APIRouter()


@router.get("")
async def get_dashboard(
    member: dict = Depends(get_current_member),
    db: Database = Depends(get_db),
):
    family_id = member["family_id"]
    member_id = member["id"]

    active_chores = await db.get_chores_by_family(family_id, status="pending")
    overdue_chores = await db.get_chores_by_family(family_id, status="overdue")
    products = await db.get_products_by_family(family_id)
    shopping = await db.get_shopping_list(family_id)
    my_chores = await db.get_chores_by_member(member_id, status="pending")

    return {
        "active_chores": len(active_chores),
        "overdue_chores": len(overdue_chores),
        "products_count": len(products),
        "shopping_pending": sum(1 for i in shopping if not i["is_bought"]),
        "my_chores": my_chores[:5],
    }
