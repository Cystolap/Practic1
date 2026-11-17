from pydantic import BaseModel, Field
from typing import Optional


class ColumnCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    position: int = 0
    wip_limit: Optional[int] = None


class ColumnRead(BaseModel):
    id: int
    board_id: int
    name: str
    position: int
    wip_limit: Optional[int] = None

    class Config:
        from_attributes = True
