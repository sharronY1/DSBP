"""
Invitation schemas
"""
from pydantic import BaseModel, EmailStr
from datetime import datetime


class InvitationCreate(BaseModel):
    email: EmailStr
    project_id: int


class InvitationResponse(BaseModel):
    id: int
    email: str
    project_id: int
    inviter_id: int
    is_accepted: bool
    expires_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

