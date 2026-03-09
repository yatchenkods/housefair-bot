from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..models import Member
from ..schemas import MemberCreate, MemberRead, MemberUpdate
from ..deps import get_session

router = APIRouter(prefix="/api/members", tags=["members"])


@router.post("", response_model=MemberRead, status_code=201)
def create_member(payload: MemberCreate, session: Session = Depends(get_session)):
    member = Member(**payload.model_dump())
    session.add(member)
    session.commit()
    session.refresh(member)
    return member


@router.get("", response_model=list[MemberRead])
def list_members(family_id: int | None = None, user_id: int | None = None, session: Session = Depends(get_session)):
    q = select(Member)
    if family_id is not None:
        q = q.where(Member.family_id == family_id)
    if user_id is not None:
        q = q.where(Member.user_id == user_id)
    return session.exec(q).all()


@router.get("/by_user", response_model=MemberRead)
def get_member_by_user(user_id: int, family_id: int, session: Session = Depends(get_session)):
    member = session.exec(
        select(Member).where(Member.user_id == user_id, Member.family_id == family_id)
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


@router.patch("/{member_id}", response_model=MemberRead)
def update_member(member_id: int, payload: MemberUpdate, session: Session = Depends(get_session)):
    member = session.get(Member, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(member, key, value)
    session.add(member)
    session.commit()
    session.refresh(member)
    return member
