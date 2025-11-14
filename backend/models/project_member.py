"""
Project Member Model
"""
from sqlalchemy import Column, BigInteger, DateTime, ForeignKey, UniqueConstraint, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base


class ProjectMember(Base):
    __tablename__ = "project_members"
    
    id = Column(BigInteger, primary_key=True, index=True)
    project_id = Column(BigInteger, ForeignKey("projects.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    role = Column(String(50), default="member", nullable=False)  # member, admin
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="project_memberships")
    
    __table_args__ = (
        UniqueConstraint('project_id', 'user_id', name='unique_project_member'),
    )

