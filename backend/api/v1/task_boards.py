"""
Task Board endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.models import TaskBoard, Project, ProjectMember, User
from backend.schemas import TaskBoardCreate, TaskBoardResponse, TaskBoardUpdate
from backend.dependencies import get_current_user
from backend.utils.license import can_create_board, update_license_count

router = APIRouter()


@router.post("", response_model=TaskBoardResponse, status_code=status.HTTP_201_CREATED)
async def create_task_board(
    board_data: TaskBoardCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new task board"""
    # Check if project exists and user has access
    project = db.query(Project).filter(Project.id == board_data.project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check access
    has_access = (
        project.owner_id == current_user.id or
        db.query(ProjectMember).filter(
            ProjectMember.project_id == board_data.project_id,
            ProjectMember.user_id == current_user.id
        ).first() is not None
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this project"
        )
    
    # Check license limit (only for project owners)
    if project.owner_id == current_user.id:
        can_create, error_message = can_create_board(db, current_user)
        if not can_create:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_message
            )
    
    # Create board
    new_board = TaskBoard(
        name=board_data.name,
        project_id=board_data.project_id,
        position=board_data.position or 0,
    )
    
    db.add(new_board)
    db.commit()
    db.refresh(new_board)
    
    # Update license count
    if project.owner_id == current_user.id:
        update_license_count(db, current_user.id)
    
    return TaskBoardResponse.from_orm(new_board)


@router.get("/project/{project_id}", response_model=List[TaskBoardResponse])
async def get_project_boards(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all task boards for a project"""
    # Check if project exists and user has access
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check access
    has_access = (
        project.owner_id == current_user.id or
        db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id
        ).first() is not None
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this project"
        )
    
    boards = db.query(TaskBoard).filter(
        TaskBoard.project_id == project_id
    ).order_by(TaskBoard.position).all()
    
    return [TaskBoardResponse.from_orm(b) for b in boards]


@router.get("/{board_id}", response_model=TaskBoardResponse)
async def get_task_board(
    board_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific task board"""
    board = db.query(TaskBoard).filter(TaskBoard.id == board_id).first()
    
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task board not found"
        )
    
    # Check access through project
    project = db.query(Project).filter(Project.id == board.project_id).first()
    has_access = (
        project.owner_id == current_user.id or
        db.query(ProjectMember).filter(
            ProjectMember.project_id == board.project_id,
            ProjectMember.user_id == current_user.id
        ).first() is not None
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this task board"
        )
    
    return TaskBoardResponse.from_orm(board)


@router.patch("/{board_id}", response_model=TaskBoardResponse)
async def update_task_board(
    board_id: int,
    board_data: TaskBoardUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a task board"""
    board = db.query(TaskBoard).filter(TaskBoard.id == board_id).first()
    
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task board not found"
        )
    
    # Check access
    project = db.query(Project).filter(Project.id == board.project_id).first()
    has_access = (
        project.owner_id == current_user.id or
        db.query(ProjectMember).filter(
            ProjectMember.project_id == board.project_id,
            ProjectMember.user_id == current_user.id
        ).first() is not None
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this task board"
        )
    
    # Update fields
    if board_data.name is not None:
        board.name = board_data.name
    if board_data.position is not None:
        board.position = board_data.position
    
    db.commit()
    db.refresh(board)
    
    return TaskBoardResponse.from_orm(board)


@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_board(
    board_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a task board"""
    board = db.query(TaskBoard).filter(TaskBoard.id == board_id).first()
    
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task board not found"
        )
    
    # Check if user is project owner
    project = db.query(Project).filter(Project.id == board.project_id).first()
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can delete task boards"
        )
    
    db.delete(board)
    db.commit()
    
    # Update license count
    update_license_count(db, current_user.id)
    
    return None

