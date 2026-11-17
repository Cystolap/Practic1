from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class CommentCreate(BaseModel):
    text: str = Field(..., min_length=1)


class CommentRead(BaseModel):
    id: int
    card_id: int
    user_id: int
    text: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
