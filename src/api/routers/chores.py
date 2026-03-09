import random
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..models import Chore, Member
from ..schemas import ChoreCreate, ChoreRead, ChoreUpdate, AssignRequest, CompleteRequest
from ..deps import get_session

router = APIRouter(prefix="/api/chores", tags=["chores"])


@router.post("", response_model=ChoreRead, status_code=201)
def create_chore(payload: ChoreCreate, session: Session = Depends(get_session)):
    chore = Chore(**payload.model_dump())
    session.add(chore)
    session.commit()
    session.refresh(chore)
    return chore


@router.get("/history", response_model=list[ChoreRead])
def get_history(
    family_id: int,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
    session: Session = Depends(get_session),
):
    q = select(Chore).where(Chore.family_id == family_id, Chore.status == "completed")
    if from_dt:
        q = q.where(Chore.completed_at >= from_dt)
    if to_dt:
        q = q.where(Chore.completed_at <= to_dt)
    return session.exec(q).all()


@router.get("", response_model=list[ChoreRead])
def list_chores(
    family_id: Optional[int] = None,
    assigned_to: Optional[int] = None,
    status: Optional[str] = None,
    session: Session = Depends(get_session),
):
    q = select(Chore)
    if family_id is not None:
        q = q.where(Chore.family_id == family_id)
    if assigned_to is not None:
        q = q.where(Chore.assigned_to == assigned_to)
    if status is not None:
        q = q.where(Chore.status == status)
    return session.exec(q).all()


@router.patch("/{chore_id}", response_model=ChoreRead)
def update_chore(chore_id: int, payload: ChoreUpdate, session: Session = Depends(get_session)):
    chore = session.get(Chore, chore_id)
    if not chore:
        raise HTTPException(status_code=404, detail="Chore not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(chore, field, value)
    session.add(chore)
    session.commit()
    session.refresh(chore)
    return chore


@router.post("/{chore_id}/assign", response_model=ChoreRead)
def assign_chore(chore_id: int, payload: AssignRequest, session: Session = Depends(get_session)):
    chore = session.get(Chore, chore_id)
    if not chore:
        raise HTTPException(status_code=404, detail="Chore not found")

    members = session.exec(select(Member).where(Member.family_id == chore.family_id)).all()
    if not members:
        raise HTTPException(status_code=400, detail="No members in family")

    if payload.mode == "manual":
        chore.assigned_to = payload.assigned_to
    elif payload.mode == "random":
        chore.assigned_to = random.choice(members).id
    elif payload.mode == "rotation":
        member_ids = [m.id for m in members]
        if chore.assigned_to in member_ids:
            idx = (member_ids.index(chore.assigned_to) + 1) % len(member_ids)
        else:
            idx = 0
        chore.assigned_to = member_ids[idx]
    elif payload.mode == "free":
        chore.assigned_to = None
    else:
        raise HTTPException(status_code=400, detail=f"Unknown mode: {payload.mode}")

    session.add(chore)
    session.commit()
    session.refresh(chore)
    return chore


@router.post("/{chore_id}/complete", response_model=ChoreRead)
def complete_chore(chore_id: int, payload: CompleteRequest, session: Session = Depends(get_session)):
    chore = session.get(Chore, chore_id)
    if not chore:
        raise HTTPException(status_code=404, detail="Chore not found")
    chore.status = "completed"
    chore.completed_at = datetime.now(timezone.utc)
    if payload.photo_url:
        chore.photo_url = payload.photo_url
    session.add(chore)
    session.commit()
    session.refresh(chore)
    return chore
