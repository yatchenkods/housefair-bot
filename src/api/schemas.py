from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class FamilyCreate(BaseModel):
    name: str
    chat_id: int
    timezone: str = "UTC"


class FamilyRead(BaseModel):
    id: int
    name: str
    chat_id: int
    created_at: datetime
    timezone: str

    model_config = {"from_attributes": True}


class MemberCreate(BaseModel):
    family_id: int
    user_id: int
    username: Optional[str] = None
    display_name: str
    role: str = "member"


class MemberRead(BaseModel):
    id: int
    family_id: int
    user_id: int
    username: Optional[str] = None
    display_name: str
    role: str
    joined_at: datetime

    model_config = {"from_attributes": True}


class ChoreCreate(BaseModel):
    family_id: int
    title: str
    description: Optional[str] = None
    chore_type: str = "one_time"
    category: Optional[str] = None
    created_by: int
    due_date: Optional[datetime] = None


class ChoreRead(BaseModel):
    id: int
    family_id: int
    title: str
    description: Optional[str] = None
    chore_type: str
    category: Optional[str] = None
    assigned_to: Optional[int] = None
    created_by: int
    created_at: datetime
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str
    photo_url: Optional[str] = None

    model_config = {"from_attributes": True}


class ChoreUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    chore_type: Optional[str] = None
    category: Optional[str] = None
    assigned_to: Optional[int] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = None
    photo_url: Optional[str] = None


class MemberUpdate(BaseModel):
    role: Optional[str] = None


class AssignRequest(BaseModel):
    mode: str = "manual"  # manual/random/rotation/free
    assigned_to: Optional[int] = None  # for manual mode


class CompleteRequest(BaseModel):
    user_id: int
    photo_url: Optional[str] = None
