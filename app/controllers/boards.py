from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel, Field

from app.database import get_db
from app.models import Board, Project
from app.controllers.auth import get_current_user, require_role

router = APIRouter()


class BoardCreate(BaseModel):
    project_id: int
    name: str = Field(..., min_length=1, max_length=255)


class BoardRead(BaseModel):
    id: int
    project_id: int
    name: str

    class Config:
        from_attributes = True


@router.get("/project/{project_id}", response_model=List[BoardRead])
def list_boards(project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Board).filter(Board.project_id == project_id).all()


@router.post("/", response_model=BoardRead, status_code=201)
def create_board(data: BoardCreate, db: Session = Depends(get_db), user=Depends(require_role(["admin", "manager"]))):
    project = db.query(Project).filter(Project.id == data.project_id).first()
    if not project:
        raise HTTPException(404, "Проект не найден")
    board = Board(project_id=data.project_id, name=data.name)
    db.add(board)
    db.commit()
    db.refresh(board)
    return board
