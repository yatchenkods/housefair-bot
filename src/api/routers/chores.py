from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.api.deps import get_current_member, get_db
from src.database.models import Chore
from src.database.repository import Database

router = APIRouter()


class ChoreCreate(BaseModel):
    title: str
    description: str = ""
    chore_type: str = "one_time"
    category: str = ""
    assigned_to: Optional[int] = None
    due_date: Optional[str] = None


@router.get("")
async def list_chores(
    status: Optional[str] = None,
    member: dict = Depends(get_current_member),
    db: Database = Depends(get_db),
):
    return await db.get_chores_by_family(member["family_id"], status=status)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_chore(
    body: ChoreCreate,
    member: dict = Depends(get_current_member),
    db: Database = Depends(get_db),
):
    from datetime import datetime

    due_date = None
    if body.due_date:
        try:
            due_date = datetime.fromisoformat(body.due_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid due_date format")

    chore = Chore(
        family_id=member["family_id"],
        title=body.title,
        description=body.description,
        chore_type=body.chore_type,
        category=body.category,
        assigned_to=body.assigned_to,
        created_by=member["id"],
        due_date=due_date,
    )
    chore_id = await db.create_chore(chore)
    return await db.get_chore(chore_id)


@router.patch("/{chore_id}/done")
async def mark_done(
    chore_id: int,
    member: dict = Depends(get_current_member),
    db: Database = Depends(get_db),
):
    chore = await db.get_chore(chore_id)
    if not chore or chore["family_id"] != member["family_id"]:
        raise HTTPException(status_code=404, detail="Chore not found")
    await db.complete_chore(chore_id)
    return await db.get_chore(chore_id)


@router.delete("/{chore_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chore(
    chore_id: int,
    member: dict = Depends(get_current_member),
    db: Database = Depends(get_db),
):
    chore = await db.get_chore(chore_id)
    if not chore or chore["family_id"] != member["family_id"]:
        raise HTTPException(status_code=404, detail="Chore not found")
    await db.delete_chore(chore_id)
