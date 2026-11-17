from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.project import ProjectCreate, ProjectRead
from app.services.project_service import create_new_project, get_user_projects

from app.controllers.auth import get_current_user, require_role
from app.models import Project

router = APIRouter()


@router.get("/", response_model=List[ProjectRead], summary="Список проектов")
def list_projects(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    
    return get_user_projects(db, current_user["id"], current_user["role"])


@router.post("/", response_model=ProjectRead, status_code=201, summary="Создать проект")
def create_project(
        project_data: ProjectCreate,
        current_user: dict = Depends(require_role(["admin", "manager"])),  # Создавать могут не все
        db: Session = Depends(get_db)
):
    return create_new_project(db, project_data, current_user["id"])



@router.delete("/{project_id}", summary="Удалить проект")
def delete_project(
        project_id: int,
        current_user: dict = Depends(require_role(["admin", "manager"])),  # Только админ и менеджер
        db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")

    db.delete(project)
    db.commit()
    return {"message": "Проект успешно удален"}


@router.patch("/{project_id}", response_model=ProjectRead, summary="Редактировать проект")
def update_project(
        project_id: int,
        project_data: ProjectCreate,
        current_user: dict = Depends(require_role(["admin", "manager"])),
        db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    project.name = project_data.name
    project.description = project_data.description
    db.commit()
    db.refresh(project)
    return project
