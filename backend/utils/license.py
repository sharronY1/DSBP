"""
License management utilities
"""
from typing import Tuple
from sqlalchemy.orm import Session
from backend.models import User, License, TaskBoard
from backend.config import settings


def get_user_board_limit(user: User) -> int:
    """Get the board limit for a user based on their license type"""
    if user.license_type.value == "paid":
        return settings.PAID_USER_BOARD_LIMIT  # -1 means unlimited
    return settings.FREE_USER_BOARD_LIMIT


def can_create_board(db: Session, user: User) -> Tuple[bool, str]:
    """Check if user can create a new board"""
    limit = get_user_board_limit(user)
    
    # Unlimited for paid users
    if limit == -1:
        return True, ""
    
    # Count existing boards
    board_count = db.query(TaskBoard).join(TaskBoard.project).filter(
        TaskBoard.project.has(owner_id=user.id)
    ).count()
    
    # Also count boards in projects where user is a member
    member_project_ids = [pm.project_id for pm in user.project_memberships]
    if member_project_ids:
        member_board_count = db.query(TaskBoard).filter(
            TaskBoard.project_id.in_(member_project_ids)
        ).count()
        board_count += member_board_count
    
    if board_count >= limit:
        return False, f"You have reached the limit of {limit} boards for free users. Please upgrade to create more boards."
    
    return True, ""


def update_license_count(db: Session, user_id: int):
    """Update the license count for a user"""
    board_count = db.query(TaskBoard).join(TaskBoard.project).filter(
        TaskBoard.project.has(owner_id=user_id)
    ).count()
    
    license_record = db.query(License).filter(License.user_id == user_id).first()
    if license_record:
        license_record.board_count = board_count
    else:
        license_record = License(user_id=user_id, board_count=board_count)
        db.add(license_record)
    
    db.commit()

