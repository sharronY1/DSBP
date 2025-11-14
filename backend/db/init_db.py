"""
Initialize database with tables
"""
from backend.database import engine, Base
from backend.models import (
    User, Project, TaskBoard, Task, ProjectMember, Invitation, License
)

def init_db():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()

