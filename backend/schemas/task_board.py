"""
Task Board schemas
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class TaskBoardCreate(BaseModel):
    name: str
    project_id: int
    position: Optional[int] = 0


class TaskBoardUpdate(BaseModel):
    name: Optional[str] = None
    position: Optional[int] = None


class TaskBoardResponse(BaseModel):
    id: int
    name: str
    project_id: int
    position: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TaskBoardWithTasks(TaskBoardResponse):
    tasks: List = []  # List["TaskResponse"]

