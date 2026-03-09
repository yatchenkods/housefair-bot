from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.api.deps import get_current_member, get_db
from src.database.models import Product
from src.database.repository import Database

router = APIRouter()


class ProductCreate(BaseModel):
    name: str
    quantity: float = 1.0
    unit: str = "шт"
    category: str = ""
    expiry_date: str = None


@router.get("")
async def list_products(
    member: dict = Depends(get_current_member),
    db: Database = Depends(get_db),
):
    return await db.get_products_by_family(member["family_id"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_product(
    body: ProductCreate,
    member: dict = Depends(get_current_member),
    db: Database = Depends(get_db),
):
    product = Product(
        family_id=member["family_id"],
        name=body.name,
        quantity=body.quantity,
        unit=body.unit,
        category=body.category,
        expiry_date=body.expiry_date,
        added_by=member["id"],
    )
    product_id = await db.add_product(product)
    return await db.get_product(product_id)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    member: dict = Depends(get_current_member),
    db: Database = Depends(get_db),
):
    product = await db.get_product(product_id)
    if not product or product["family_id"] != member["family_id"]:
        raise HTTPException(status_code=404, detail="Product not found")
    await db.remove_product(product_id)
