"""
Task Board Model
"""
from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base


class TaskBoard(Base):
    __tablename__ = "task_boards"
    
    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    project_id = Column(BigInteger, ForeignKey("projects.id"), nullable=False)
    position = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    project = relationship("Project", back_populates="task_boards")
    tasks = relationship("Task", back_populates="board", cascade="all, delete-orphan", order_by="Task.position")

