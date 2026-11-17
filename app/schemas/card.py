from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class CardCreate(BaseModel):
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
