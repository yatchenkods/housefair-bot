from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..models import Family
from ..schemas import FamilyCreate, FamilyRead
from ..deps import get_session

router = APIRouter(prefix="/api/families", tags=["families"])


@router.post("", response_model=FamilyRead, status_code=201)
def create_family(payload: FamilyCreate, session: Session = Depends(get_session)):
    existing = session.exec(select(Family).where(Family.chat_id == payload.chat_id)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Family with this chat_id already exists")
    family = Family(**payload.model_dump())
    session.add(family)
    session.commit()
    session.refresh(family)
    return family


@router.get("", response_model=list[FamilyRead])
def list_families(session: Session = Depends(get_session)):
    return session.exec(select(Family)).all()


@router.get("/by_id/{family_id}", response_model=FamilyRead)
def get_family_by_id(family_id: int, session: Session = Depends(get_session)):
    family = session.get(Family, family_id)
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")
    return family


@router.get("/{chat_id}", response_model=FamilyRead)
def get_family_by_chat(chat_id: int, session: Session = Depends(get_session)):
    family = session.exec(select(Family).where(Family.chat_id == chat_id)).first()
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")
    return family
