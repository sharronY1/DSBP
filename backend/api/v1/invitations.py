"""
Invitation endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List
import secrets
from backend.database import get_db
from backend.models import Invitation, Project, ProjectMember, User
from backend.schemas import InvitationCreate, InvitationResponse
from backend.dependencies import get_current_user
from backend.utils.email import send_invitation_email
from backend.config import settings

router = APIRouter()


@router.post("", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    invitation_data: InvitationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create and send an invitation"""
    # Check if project exists
    project = db.query(Project).filter(Project.id == invitation_data.project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if user is project owner or member
    is_owner = project.owner_id == current_user.id
    is_member = db.query(ProjectMember).filter(
        ProjectMember.project_id == invitation_data.project_id,
        ProjectMember.user_id == current_user.id
    ).first() is not None
    
    if not is_owner and not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to invite users to this project"
        )
    
    # Check if user is already a member
    existing_user = db.query(User).filter(User.email == invitation_data.email).first()
    if existing_user:
        existing_member = db.query(ProjectMember).filter(
            ProjectMember.project_id == invitation_data.project_id,
            ProjectMember.user_id == existing_user.id
        ).first()
        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this project"
            )
    
    # Check if there's a pending invitation
    existing_invitation = db.query(Invitation).filter(
        Invitation.email == invitation_data.email,
        Invitation.project_id == invitation_data.project_id,
        Invitation.is_accepted == False,
        Invitation.expires_at > datetime.utcnow()
    ).first()
    
    if existing_invitation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An active invitation already exists for this email"
        )
    
    # Create invitation
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=7)
    
    new_invitation = Invitation(
        email=invitation_data.email,
        project_id=invitation_data.project_id,
        inviter_id=current_user.id,
        token=token,
        expires_at=expires_at,
    )
    
    db.add(new_invitation)
    db.commit()
    db.refresh(new_invitation)
    
    # Send invitation email
    invitation_url = f"{settings.CORS_ORIGINS.split(',')[0]}/accept-invitation"
    await send_invitation_email(
        to_email=invitation_data.email,
        inviter_name=current_user.full_name or current_user.username,
        project_name=project.name,
        invitation_token=token,
        invitation_url=invitation_url,
    )
    
    return InvitationResponse.from_orm(new_invitation)


@router.get("/project/{project_id}", response_model=List[InvitationResponse])
async def get_project_invitations(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all invitations for a project"""
    # Check access
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    is_owner = project.owner_id == current_user.id
    is_member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == current_user.id
    ).first() is not None
    
    if not is_owner and not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this project"
        )
    
    invitations = db.query(Invitation).filter(
        Invitation.project_id == project_id
    ).order_by(Invitation.created_at.desc()).all()
    
    return [InvitationResponse.from_orm(inv) for inv in invitations]


@router.post("/accept/{token}", response_model=dict)
async def accept_invitation(
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Accept an invitation"""
    invitation = db.query(Invitation).filter(
        Invitation.token == token,
        Invitation.is_accepted == False,
        Invitation.expires_at > datetime.utcnow()
    ).first()
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired invitation"
        )
    
    # Check if email matches
    if invitation.email.lower() != current_user.email.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invitation was sent to a different email address"
        )
    
    # Check if already a member
    existing_member = db.query(ProjectMember).filter(
        ProjectMember.project_id == invitation.project_id,
        ProjectMember.user_id == current_user.id
    ).first()
    
    if existing_member:
        # Mark invitation as accepted anyway
        invitation.is_accepted = True
        db.commit()
        return {"message": "You are already a member of this project"}
    
    # Add user as project member
    project_member = ProjectMember(
        project_id=invitation.project_id,
        user_id=current_user.id,
        role="member",
    )
    db.add(project_member)
    
    # Mark invitation as accepted
    invitation.is_accepted = True
    db.commit()
    
    return {"message": "Invitation accepted successfully"}

