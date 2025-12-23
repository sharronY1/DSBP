from datetime import datetime
from html import escape
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer


class UserCreate(BaseModel):
    username: str = Field(..., max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = ""
    visibility: Literal["all", "private", "selected"] = "all"


class ProjectCreate(ProjectBase):
    shared_usernames: List[str] = Field(default_factory=list)


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    visibility: Optional[Literal["all", "private", "selected"]] = None
    shared_usernames: Optional[List[str]] = None


class ProjectOut(ProjectBase):
    id: int
    owner_id: int
    created_at: datetime
    shared_users: List["UserOut"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = ""
    status: Literal["new_task", "scheduled", "in_progress", "completed"] = "new_task"


class TaskCreate(TaskBase):
    project_id: int
    due_date: Optional[datetime] = None
    assignee_ids: List[int] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=150)
    description: Optional[str] = None
    status: Optional[Literal["new_task", "scheduled", "in_progress", "completed"]] = None
    due_date: Optional[datetime] = None
    assignee_ids: Optional[List[int]] = None


class TaskOut(TaskBase):
    id: int
    project_id: int
    created_at: datetime
    due_date: Optional[datetime] = None
    assignees: List["UserOut"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TaskSummary(BaseModel):
    id: int
    title: str
    project_id: int
    project_name: str


class TaskDependencyBase(BaseModel):
    dependent_task_id: int
    depends_on_task_id: int


class TaskDependencyCreate(TaskDependencyBase):
    pass


class TaskDependencyOut(TaskDependencyBase):
    id: int
    dependent_task: TaskOut
    depends_on_task: TaskOut
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DependencyEdgeOut(BaseModel):
    id: int
    dependent: TaskSummary
    depends_on: TaskSummary


class DependencyChainOut(BaseModel):
    tasks: List[TaskSummary]


class DependencyConvergenceOut(BaseModel):
    target: TaskSummary
    sources: List[TaskSummary]


class DependencyMapOut(BaseModel):
    tasks: List[TaskSummary]
    edges: List[DependencyEdgeOut]
    chains: List[DependencyChainOut]
    convergences: List[DependencyConvergenceOut]


class CommentCreate(BaseModel):
    task_id: int
    content: str
    parent_id: Optional[int] = None


class CommentOut(BaseModel):
    id: int
    content: str
    created_at: datetime
    solved: bool
    task_id: int
    author: UserOut
    parent_id: Optional[int]
    replies: List["CommentOut"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("content")
    def sanitize_content(self, value: str) -> str:
        return escape(value or "")
    
    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        """Ensure datetime is returned as UTC ISO format with 'Z' suffix"""
        if value.tzinfo is None:
            # Treat naive datetime as UTC
            return value.isoformat() + "Z"
        return value.isoformat()


CommentOut.model_rebuild()


class NotificationOut(BaseModel):
    id: int
    comment_id: int
    message: str
    read: bool
    created_at: datetime
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    task_id: Optional[int] = None
    task_title: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        """Ensure datetime is returned as UTC ISO format with 'Z' suffix"""
        if value.tzinfo is None:
            # Treat naive datetime as UTC
            return value.isoformat() + "Z"
        return value.isoformat()


class TaskActivityOut(BaseModel):
    id: int
    action: Literal["created", "deleted", "status_changed"]
    status: Optional[str] = None
    task_id: Optional[int] = None
    task_title: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectDashboardOut(BaseModel):
    project_id: int
    total_tasks: int
    status_counts: Dict[str, int]
    updated_at: datetime


class TaskHistoryResponse(BaseModel):
    activities: List[TaskActivityOut]
    daily_counts: Dict[str, int]


class LicenseActivate(BaseModel):
    license_key: str = Field(..., description="License key in format AAAA-BBBB-CCCC-DDDD")


class LicenseOut(BaseModel):
    id: int
    license_key: str
    activated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LicenseStatus(BaseModel):
    has_license: bool
    license_key: Optional[str] = None
    activated_at: Optional[datetime] = None