from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.database import get_db
from app.models import Card, BoardColumn, History
from app.controllers.auth import get_current_user

router = APIRouter()


class CardCreate(BaseModel):
    column_id: int
    title: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    priority: str = "Medium"
    assignee_id: Optional[int] = None
    deadline: Optional[datetime] = None
    labels: str = ""
    position: int = 0


class CardUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    assignee_id: Optional[int] = None
    deadline: Optional[datetime] = None
    labels: Optional[str] = None
    column_id: Optional[int] = None
    position: Optional[int] = None


class CardRead(BaseModel):
    id: int
    column_id: int
    title: str
    description: str
    priority: str
    assignee_id: Optional[int] = None
    deadline: Optional[datetime] = None
    labels: str
    position: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


@router.get("/column/{column_id}", response_model=List[CardRead])
def list_cards(column_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Card).filter(Card.column_id == column_id).order_by(Card.position).all()


@router.post("/", response_model=CardRead, status_code=201)
def create_card(data: CardCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    col = db.query(BoardColumn).filter(BoardColumn.id == data.column_id).first()
    if not col:
        raise HTTPException(404, "Колонка не найдена")
    if col.wip_limit is not None:
        count = db.query(Card).filter(Card.column_id == data.column_id).count()
        if count >= col.wip_limit:
            raise HTTPException(400, f"WIP-лимит колонки: {col.wip_limit}")
    card = Card(**data.model_dump())
    db.add(card)
    db.flush()
    db.add(History(card_id=card.id, user_id=user["id"], action=f"Создана: {card.title}"))
    db.commit()
    db.refresh(card)
    return card


@router.patch("/{card_id}", response_model=CardRead)
def update_card(card_id: int, data: CardUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(404, "Карточка не найдена")
    payload = data.model_dump(exclude_unset=True)
    # WIP проверка при перемещении карточки
    if "column_id" in payload and payload["column_id"] != card.column_id:
        col = db.query(BoardColumn).filter(BoardColumn.id == payload["column_id"]).first()
        if col and col.wip_limit is not None:
            count = db.query(Card).filter(Card.column_id == payload["column_id"]).count()
            if count >= col.wip_limit:
                raise HTTPException(400, f"WIP-лимит колонки: {col.wip_limit}")
    for k, v in payload.items():
        setattr(card, k, v)
    db.add(History(card_id=card.id, user_id=user["id"], action=f"Обновлена: {card.title}"))
    db.commit()
    db.refresh(card)
    return card


@router.delete("/{card_id}")
def delete_card(card_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(404, "Карточка не найдена")
    db.delete(card)
    db.commit()
    return {"message": "Карточка удалена"}
