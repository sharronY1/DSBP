import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

import app.api.routes as routes
import app.schemas as schemas
import app.services.auth as auth
from tests.factories import create_project, create_task, create_user


def test_user_registration_creates_hashed_password(db_session: Session):
    """TC-API-01: User Registration Creates Hashed Password - User registration data provided."""
    user = create_user(db_session, "alice", "alice@example.com", password="secret123")
    assert user.username == "alice"
    assert user.email == "alice@example.com"
    assert user.hashed_password != "secret123"
    assert auth.verify_password("secret123", user.hashed_password)


def test_user_registration_prevents_duplicate_usernames(db_session: Session):
    """TC-API-02: User Registration Prevents Duplicate Usernames - User with username exists."""
    create_user(db_session, "bob", "bob@example.com")

    with pytest.raises(HTTPException) as exc:
        create_user(db_session, "bob", "bob2@example.com")
    assert exc.value.status_code == 400
    assert exc.value.detail == "Username already registered"


def test_user_registration_prevents_duplicate_emails(db_session: Session):
    """TC-API-03: User Registration Prevents Duplicate Emails - User with email exists."""
    create_user(db_session, "carol", "carol@example.com")

    with pytest.raises(HTTPException) as exc:
        create_user(db_session, "carol2", "carol@example.com")
    assert exc.value.status_code == 400
    assert exc.value.detail == "Email already registered"


def test_user_login_returns_bearer_token(db_session: Session):
    """TC-API-04: User Login Returns Bearer Token - Valid user credentials provided."""
    create_user(db_session, "dave", "dave@example.com", password="strongpass")

    token = routes.login(schemas.UserLogin(username="dave", password="strongpass"), db_session)
    assert token.access_token
    assert token.token_type == "bearer"


def test_user_login_rejects_invalid_password(db_session: Session):
    """TC-API-05: User Login Rejects Invalid Password - User exists with different password."""
    create_user(db_session, "erin", "erin@example.com", password="strongpass")

    with pytest.raises(HTTPException) as exc:
        routes.login(schemas.UserLogin(username="erin", password="wrong"), db_session)
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid credentials"


def test_user_login_rejects_unknown_user(db_session: Session):
    """TC-API-06: User Login Rejects Unknown User - User does not exist."""
    create_user(db_session, "frank", "frank@example.com", password="strongpass")

    with pytest.raises(HTTPException) as exc:
        routes.login(schemas.UserLogin(username="ghost", password="whatever"), db_session)
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid credentials"


def test_dependency_map_returns_chains_and_edges(db_session: Session):
    """TC-API-07: Dependency Map Returns Chains and Edges - Tasks with dependencies exist."""
    owner = create_user(db_session, "grace", "grace@example.com")
    project = create_project(db_session, owner, name="Backend")

    task_setup = create_task(db_session, owner, project, title="Setup")
    task_build = create_task(db_session, owner, project, title="Build")
    task_test = create_task(db_session, owner, project, title="Test")

    dep_inputs = [
        schemas.TaskDependencyCreate(depends_on_task_id=task_setup.id, dependent_task_id=task_build.id),
        schemas.TaskDependencyCreate(depends_on_task_id=task_build.id, dependent_task_id=task_test.id),
    ]
    for dependency_in in dep_inputs:
        routes.create_task_dependency(dependency_in, db_session, owner)

    dependency_map = routes.dependency_map(db_session, owner)

    assert len(dependency_map.tasks) == 3
    assert len(dependency_map.edges) == 2
    assert dependency_map.chains
    chain_titles = [task.title for task in dependency_map.chains[0].tasks]
    assert chain_titles == ["Setup", "Build", "Test"]


def test_dependency_map_returns_empty_structure_when_user_has_no_tasks(db_session: Session):
    """TC-API-08: Dependency Map Returns Empty Structure - User has no tasks."""
    owner = create_user(db_session, "henry", "henry@example.com")

    dependency_map = routes.dependency_map(db_session, owner)

    assert dependency_map.tasks == []
    assert dependency_map.edges == []
    assert dependency_map.chains == []
    assert dependency_map.convergences == []


def test_dependency_map_identifies_convergences(db_session: Session):
    """TC-API-09: Dependency Map Identifies Convergences - Tasks with converging dependencies exist."""
    owner = create_user(db_session, "irene", "irene@example.com")
    project = create_project(db_session, owner, name="Infra")

    task_a = create_task(db_session, owner, project, title="Plan")
    task_b = create_task(db_session, owner, project, title="Build")
    task_c = create_task(db_session, owner, project, title="Review")

    dep_inputs = [
        schemas.TaskDependencyCreate(depends_on_task_id=task_a.id, dependent_task_id=task_c.id),
        schemas.TaskDependencyCreate(depends_on_task_id=task_b.id, dependent_task_id=task_c.id),
    ]
    for dependency_in in dep_inputs:
        routes.create_task_dependency(dependency_in, db_session, owner)

    dependency_map = routes.dependency_map(db_session, owner)

    assert len(dependency_map.convergences) == 1
    convergence = dependency_map.convergences[0]
    assert convergence.target.title == "Review"
    assert sorted(task.title for task in convergence.sources) == ["Build", "Plan"]


def test_notifications_created_from_mentions(db_session: Session):
    """TC-API-10: Notifications Created From Mentions - Comment with mention is created."""
    owner = create_user(db_session, "jack", "jack@example.com")
    guest = create_user(db_session, "kate", "kate@example.com")

    project = create_project(db_session, owner, name="Docs")
    task = create_task(db_session, owner, project, title="Write docs")

    comment_in = schemas.CommentCreate(task_id=task.id, content=f"Heads up @{guest.username}")
    routes.create_comment(comment_in, db_session, owner)

    notifications = routes.list_notifications(db_session, guest)
    assert len(notifications) == 1
    notification = notifications[0]
    assert notification.message.startswith(f"{owner.username} mentioned you")
    assert notification.task_id == task.id

    updated = routes.mark_notification_read(notification.id, db_session, guest)
    assert updated.read is True


def test_notifications_include_self_mentions(db_session: Session):
    """TC-API-11: Notifications Include Self Mentions - User mentions themselves in comment."""
    owner = create_user(db_session, "liam", "liam@example.com")

    project = create_project(db_session, owner, name="Website")
    task = create_task(db_session, owner, project, title="Deploy")

    comment_in = schemas.CommentCreate(task_id=task.id, content="Reminder for @liam")
    routes.create_comment(comment_in, db_session, owner)

    notifications = routes.list_notifications(db_session, owner)
    assert len(notifications) == 1
    assert notifications[0].message.startswith(f"{owner.username} mentioned you")


def test_mark_notification_read_restricted_to_recipient(db_session: Session):
    """TC-API-12: Mark Notification Read Restricted to Recipient - Notification exists for different user."""
    owner = create_user(db_session, "maria", "maria@example.com")
    guest = create_user(db_session, "nate", "nate@example.com")
    outsider = create_user(db_session, "oliver", "oliver@example.com")

    project = create_project(db_session, owner, name="Handbook")
    task = create_task(db_session, owner, project, title="Draft")

    comment_in = schemas.CommentCreate(task_id=task.id, content="Ping @nate")
    routes.create_comment(comment_in, db_session, owner)

    notification = routes.list_notifications(db_session, guest)[0]

    with pytest.raises(HTTPException) as exc:
        routes.mark_notification_read(notification.id, db_session, outsider)
    assert exc.value.status_code == 404
    assert exc.value.detail == "Notification not found"


def test_project_private_visibility_ignores_shared_users(db_session: Session):
    """TC-API-13: Project Private Visibility Ignores Shared Users - Project created with private visibility and shared users."""
    owner = create_user(db_session, "paula", "paula@example.com")
    guest = create_user(db_session, "quentin", "quentin@example.com")

    project_in = schemas.ProjectCreate(
        name="Roadmap",
        description="",
        visibility="private",
        shared_usernames=[guest.username],
    )
    project = routes.create_project(project_in, db_session, owner)

    assert project.visibility == "private"
    assert project.shared_users == []

    guest_projects = routes.list_projects(db_session, guest)
    assert guest_projects == []


def test_project_selected_visibility_requires_known_users(db_session: Session):
    """TC-API-14: Project Selected Visibility Requires Known Users - Project created with unknown shared users."""
    owner = create_user(db_session, "rachel", "rachel@example.com")

    project_in = schemas.ProjectCreate(
        name="Playbook",
        description="",
        visibility="selected",
        shared_usernames=["unknown"],
    )

    with pytest.raises(HTTPException) as exc:
        routes.create_project(project_in, db_session, owner)
    assert exc.value.status_code == 400
    assert "Unknown users" in exc.value.detail


def test_project_visibility_update_clears_shared_users_when_opening_access(db_session: Session):
    """TC-API-15: Project Visibility Update Clears Shared Users - Project with selected visibility and shared users exists."""
    owner = create_user(db_session, "sara", "sara@example.com")
    guest = create_user(db_session, "tom", "tom@example.com")

    project = routes.create_project(
        schemas.ProjectCreate(
            name="Campaign",
            description="",
            visibility="selected",
            shared_usernames=[guest.username],
        ),
        db_session,
        owner,
    )

    assert len(project.shared_users) == 1

    updated = routes.update_project(
        project.id,
        schemas.ProjectUpdate(visibility="all"),
        db_session,
        owner,
    )

    assert updated.visibility == "all"
    assert updated.shared_users == []
