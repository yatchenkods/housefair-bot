from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Family(BaseModel):
    id: Optional[int] = None
    name: str
    chat_id: int
    created_at: Optional[datetime] = None
    timezone: str = "Europe/Moscow"
    settings: str = "{}"


class Member(BaseModel):
    id: Optional[int] = None
    family_id: int
    user_id: Optional[int] = None
    username: str
    display_name: str
    role: str = "member"
    joined_at: Optional[datetime] = None
    preferences: str = "{}"


class Chore(BaseModel):
    id: Optional[int] = None
    family_id: int
    title: str
    description: str = ""
    chore_type: str = "one_time"
    category: str = ""
    assigned_to: Optional[int] = None
    created_by: int
    created_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"
    photo_url: str = ""


class Product(BaseModel):
    id: Optional[int] = None
    family_id: int
    name: str
    quantity: float = 1.0
    unit: str = "шт"
    category: str = ""
    expiry_date: Optional[str] = None
    added_at: Optional[datetime] = None
    added_by: int = 0


class Recipe(BaseModel):
    id: Optional[int] = None
    family_id: int
    title: str
    ingredients: str = "[]"
    instructions: str = ""
    cuisine_type: str = ""
    cooking_time: int = 0
    difficulty: str = ""
    calories: int = 0
    created_at: Optional[datetime] = None
    cooked_by: Optional[int] = None
    rating: float = 0.0


class Statistics(BaseModel):
    id: Optional[int] = None
    family_id: int
    member_id: int
    period_type: str = "week"
    period_start: str = ""
    period_end: str = ""
    chores_completed: int = 0
    recipes_cooked: int = 0
    total_points: int = 0
    data: str = "{}"


class ShoppingItem(BaseModel):
    id: Optional[int] = None
    family_id: int
    name: str
    is_bought: bool = False
    added_at: Optional[datetime] = None
