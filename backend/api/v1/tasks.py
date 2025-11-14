"""
Task endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.models import Task, TaskBoard, Project, ProjectMember, User
from backend.schemas import TaskCreate, TaskResponse, TaskUpdate
from backend.dependencies import get_current_user

router = APIRouter()


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new task"""
    # Check if board exists and user has access
    board = db.query(TaskBoard).filter(TaskBoard.id == task_data.board_id).first()
    
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
    
    # Create task
    new_task = Task(
        title=task_data.title,
        description=task_data.description,
        status=task_data.status,
        board_id=task_data.board_id,
        position=task_data.position or 0,
        created_by_id=current_user.id,
        assigned_to_id=task_data.assigned_to_id,
    )
    
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    
    return TaskResponse.from_orm(new_task)


@router.get("/board/{board_id}", response_model=List[TaskResponse])
async def get_board_tasks(
    board_id: int,
    status_filter: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all tasks for a board, optionally filtered by status"""
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
    
    query = db.query(Task).filter(Task.board_id == board_id)
    
    if status_filter:
        query = query.filter(Task.status == status_filter)
    
    tasks = query.order_by(Task.position).all()
    
    return [TaskResponse.from_orm(t) for t in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific task"""
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check access
    board = db.query(TaskBoard).filter(TaskBoard.id == task.board_id).first()
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
            detail="You don't have access to this task"
        )
    
    return TaskResponse.from_orm(task)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a task"""
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check access
    board = db.query(TaskBoard).filter(TaskBoard.id == task.board_id).first()
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
            detail="You don't have access to this task"
        )
    
    # Update fields
    if task_data.title is not None:
        task.title = task_data.title
    if task_data.description is not None:
        task.description = task_data.description
    if task_data.status is not None:
        task.status = task_data.status
    if task_data.position is not None:
        task.position = task_data.position
    if task_data.assigned_to_id is not None:
        task.assigned_to_id = task_data.assigned_to_id
    
    db.commit()
    db.refresh(task)
    
    return TaskResponse.from_orm(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a task"""
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check access
    board = db.query(TaskBoard).filter(TaskBoard.id == task.board_id).first()
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
            detail="You don't have access to this task"
        )
    
    db.delete(task)
    db.commit()
    
    return None

