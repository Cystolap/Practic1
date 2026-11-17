from pydantic import BaseModel, Field
from typing import Optional, List


class BoardCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class BoardRead(BaseModel):
    id: int
    project_id: int
    name: str

    class Config:
        from_attributes = True
