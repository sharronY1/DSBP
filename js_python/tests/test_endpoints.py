"""Integration tests that exercise the FastAPI routes via TestClient."""

import html
from typing import Dict

import pytest

from tests.factories import (
    create_dependency,
    create_project,
    create_task,
    create_user,
    login_user,
)


def auth_headers(db_session, username: str, password: str = "secret123") -> Dict[str, str]:
    token = login_user(db_session, username, password)
    return {"Authorization": f"Bearer {token}"}


def test_create_dependency_rejects_cycle(api_client, db_session):
    owner = create_user(db_session, "owner", "owner@example.com")
    project = create_project(db_session, owner, name="CycleSafe")

    task_a = create_task(db_session, owner, project, title="Task A")
    task_b = create_task(db_session, owner, project, title="Task B")
    task_c = create_task(db_session, owner, project, title="Task C")

    create_dependency(db_session, owner, depends_on=task_a, dependent=task_b)
    create_dependency(db_session, owner, depends_on=task_b, dependent=task_c)

    response = api_client.post(
        "/task-dependencies",
        json={
            "depends_on_task_id": task_c.id,
            "dependent_task_id": task_a.id,
        },
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Dependency would create a cycle"


def test_create_dependency_rejects_self_loop(api_client, db_session):
    owner = create_user(db_session, "loop", "loop@example.com")
    project = create_project(db_session, owner, name="SelfLoop")
    task = create_task(db_session, owner, project, title="Standalone")

    response = api_client.post(
        "/task-dependencies",
        json={
            "depends_on_task_id": task.id,
            "dependent_task_id": task.id,
        },
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Task cannot depend on itself"


def test_dependency_cross_project_forbidden(api_client, db_session):
    owner = create_user(db_session, "proj", "proj@example.com")
    project_a = create_project(db_session, owner, name="Alpha")
    project_b = create_project(db_session, owner, name="Beta")

    task_alpha = create_task(db_session, owner, project_a, title="Alpha Task")
    task_beta = create_task(db_session, owner, project_b, title="Beta Task")

    response = api_client.post(
        "/task-dependencies",
        json={
            "depends_on_task_id": task_alpha.id,
            "dependent_task_id": task_beta.id,
        },
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Tasks must belong to the same project"


def test_task_status_transition_persists(api_client, db_session):
    owner = create_user(db_session, "status", "status@example.com")
    project = create_project(db_session, owner, name="Pipeline")
    task = create_task(db_session, owner, project, title="Draft spec")

    response = api_client.patch(
        f"/tasks/{task.id}",
        json={"status": "in_progress"},
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"

    db_session.refresh(task)
    assert task.status == "in_progress"


@pytest.mark.parametrize("path", [
    "/projects",
    "/dependency-map",
    "/notifications",
])
def test_unauthenticated_requests_return_401(api_client, path):
    response = api_client.get(path)
    assert response.status_code == 401


# def test_horizontal_privilege_escalation_blocked(api_client, db_session):
#     owner = create_user(db_session, "alice", "alice@example.net")
#     outsider = create_user(db_session, "mallory", "mallory@example.net")
#     project = create_project(db_session, owner, name="Secrets")
#     task = create_task(db_session, owner, project, title="Encrypt docs")

#     response = api_client.patch(
#         f"/tasks/{task.id}",
#         json={"status": "completed"},
#         headers=auth_headers(db_session, outsider.username),
#     )
#     assert response.status_code == 403



def test_comment_mention_creates_notification(api_client, db_session):
    owner = create_user(db_session, "writer", "writer@example.com")
    guest = create_user(db_session, "reader", "reader@example.com")
    project = create_project(
        db_session,
        owner,
        name="Docs",
        visibility="selected",
        shared_usernames=[guest.username],
    )
    task = create_task(db_session, owner, project, title="User Guide")

    response = api_client.post(
        "/comments",
        json={"task_id": task.id, "content": f"Ping @{guest.username}"},
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code == 201

    notif_response = api_client.get("/notifications", headers=auth_headers(db_session, guest.username))
    assert notif_response.status_code == 200
    notifications = notif_response.json()
    assert len(notifications) == 1
    assert "mentioned you" in notifications[0]["message"]
    assert notifications[0]["task_id"] == task.id



def test_comment_xss_payload_is_escaped(api_client, db_session):
    owner = create_user(db_session, "secure", "secure@example.com")
    project = create_project(db_session, owner, name="Security")
    task = create_task(db_session, owner, project, title="Review")

    malicious = "<script>alert('owned')</script>"
    response = api_client.post(
        "/comments",
        json={"task_id": task.id, "content": malicious},
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code == 201
    assert response.json()["content"] == html.escape(malicious)

    list_response = api_client.get(
        f"/tasks/{task.id}/comments",
        headers=auth_headers(db_session, owner.username),
    )
    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload[0]["content"] == html.escape(malicious)
