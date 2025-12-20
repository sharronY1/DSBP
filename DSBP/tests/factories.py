"""Helpers and fixtures for constructing common test entities."""

from typing import Iterable, Optional

from sqlalchemy.orm import Session

import app.api.routes as routes
import app.models as models
import app.schemas as schemas


DEFAULT_PASSWORD = "secret123"


def create_user(session: Session, username: str, email: str, password: str = DEFAULT_PASSWORD) -> models.User:
    user_in = schemas.UserCreate(username=username, email=email, password=password)
    return routes.register(user_in, session)


def create_project(
    session: Session,
    owner: models.User,
    *,
    name: str = "Demo Project",
    description: str = "",
    visibility: str = "all",
    shared_usernames: Optional[Iterable[str]] = None,
) -> models.Project:
    project_in = schemas.ProjectCreate(
        name=name,
        description=description,
        visibility=visibility,
        shared_usernames=list(shared_usernames or []),
    )
    return routes.create_project(project_in, session, owner)


def create_task(
    session: Session,
    owner: models.User,
    project: models.Project,
    *,
    title: str = "New Task",
    description: str = "",
    status: str = "new_task",
) -> models.Task:
    task_in = schemas.TaskCreate(
        title=title,
        description=description,
        status=status,
        project_id=project.id,
        assignee_ids=[],
    )
    return routes.create_task(task_in, session, owner)


def create_dependency(
    session: Session,
    owner: models.User,
    *,
    depends_on: models.Task,
    dependent: models.Task,
) -> models.TaskDependency:
    dependency_in = schemas.TaskDependencyCreate(
        depends_on_task_id=depends_on.id,
        dependent_task_id=dependent.id,
    )
    return routes.create_task_dependency(dependency_in, session, owner)


def login_user(session: Session, username: str, password: str = DEFAULT_PASSWORD) -> str:
    token = routes.login(
        schemas.UserLogin(username=username, password=password),
        session,
    )
    return token.access_token
