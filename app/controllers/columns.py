from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field

from app.database import get_db
from app.models import BoardColumn, Board
from app.controllers.auth import get_current_user, require_role

router = APIRouter()


class ColumnCreate(BaseModel):
    board_id: int
    name: str = Field(..., min_length=1, max_length=255)
    position: int = 0
    wip_limit: Optional[int] = None


class ColumnUpdate(BaseModel):
    name: Optional[str] = None
    position: Optional[int] = None
    wip_limit: Optional[int] = None


class ColumnRead(BaseModel):
    id: int
    board_id: int
    name: str
    position: int
    wip_limit: Optional[int] = None

    class Config:
        from_attributes = True


@router.get("/board/{board_id}", response_model=List[ColumnRead])
def list_columns(board_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(BoardColumn).filter(BoardColumn.board_id == board_id).order_by(BoardColumn.position).all()


@router.post("/", response_model=ColumnRead, status_code=201)
def create_column(data: ColumnCreate, db: Session = Depends(get_db), user=Depends(require_role(["admin", "manager"]))):
    board = db.query(Board).filter(Board.id == data.board_id).first()
    if not board:
        raise HTTPException(404, "Доска не найдена")
    col = BoardColumn(board_id=data.board_id, name=data.name, position=data.position, wip_limit=data.wip_limit)
    db.add(col)
    db.commit()
    db.refresh(col)
    return col


@router.patch("/{column_id}", response_model=ColumnRead)
def update_column(column_id: int, data: ColumnUpdate, db: Session = Depends(get_db), user=Depends(require_role(["admin", "manager"]))):
    col = db.query(BoardColumn).filter(BoardColumn.id == column_id).first()
    if not col:
        raise HTTPException(404, "Колонка не найдена")
    if data.name is not None:
        col.name = data.name
    if data.position is not None:
        col.position = data.position
    if data.wip_limit is not None:
        col.wip_limit = data.wip_limit
    db.commit()
    db.refresh(col)
    return col


@router.delete("/{column_id}")
def delete_column(column_id: int, db: Session = Depends(get_db), user=Depends(require_role(["admin", "manager"]))):
    col = db.query(BoardColumn).filter(BoardColumn.id == column_id).first()
    if not col:
        raise HTTPException(404, "Колонка не найдена")
    db.delete(col)
    db.commit()
    return {"message": "Колонка удалена"}
