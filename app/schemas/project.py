from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Название проекта")
    description: str = Field(default="", max_length=1000, description="Описание")


class ProjectRead(BaseModel):
    id: int
    name: str
    description: str
    owner_id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
