from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class Family(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    chat_id: int = Field(unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    timezone: str = "UTC"
    settings: Optional[str] = None  # JSON blob


class Member(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    family_id: int = Field(foreign_key="family.id")
    user_id: int
    username: Optional[str] = None
    display_name: str
    role: str = "member"  # admin / member
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    preferences: Optional[str] = None  # JSON blob


class Chore(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    family_id: int = Field(foreign_key="family.id")
    title: str
    description: Optional[str] = None
    chore_type: str = "one_time"  # one_time/daily/weekly/monthly
    category: Optional[str] = None
    assigned_to: Optional[int] = Field(default=None, foreign_key="member.id")
    created_by: int = Field(foreign_key="member.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"  # pending/completed/overdue
    photo_url: Optional[str] = None
