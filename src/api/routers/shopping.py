from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.api.deps import get_current_member, get_db
from src.database.repository import Database

router = APIRouter()


class ShoppingItemCreate(BaseModel):
    name: str


@router.get("")
async def list_shopping(
    member: dict = Depends(get_current_member),
    db: Database = Depends(get_db),
):
    return await db.get_shopping_list(member["family_id"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_item(
    body: ShoppingItemCreate,
    member: dict = Depends(get_current_member),
    db: Database = Depends(get_db),
):
    item_id = await db.add_shopping_item(member["family_id"], body.name)
    return await db.get_shopping_item(item_id)


@router.patch("/{item_id}")
async def toggle_item(
    item_id: int,
    member: dict = Depends(get_current_member),
    db: Database = Depends(get_db),
):
    item = await db.get_shopping_item(item_id)
    if not item or item["family_id"] != member["family_id"]:
        raise HTTPException(status_code=404, detail="Item not found")
    await db.toggle_shopping_item(item_id)
    return await db.get_shopping_item(item_id)


@router.delete("/bought", status_code=status.HTTP_204_NO_CONTENT)
async def clear_bought(
    member: dict = Depends(get_current_member),
    db: Database = Depends(get_db),
):
    await db.clear_bought_items(member["family_id"])


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int,
    member: dict = Depends(get_current_member),
    db: Database = Depends(get_db),
):
    item = await db.get_shopping_item(item_id)
    if not item or item["family_id"] != member["family_id"]:
        raise HTTPException(status_code=404, detail="Item not found")
    await db.delete_shopping_item(item_id)
