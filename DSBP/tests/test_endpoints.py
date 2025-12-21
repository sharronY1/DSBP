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


def test_prevent_cyclic_dependencies_2_node(api_client, db_session):
    """TC-DEP-01: Prevent Cyclic Dependencies (2-node) - Two tasks A and B exist in the same project."""
    owner = create_user(db_session, "cycle2", "cycle2@example.com")
    project = create_project(db_session, owner, name="2-Node Cycle")

    task_a = create_task(db_session, owner, project, title="Task A")
    task_b = create_task(db_session, owner, project, title="Task B")

    # Add A depends on B
    response1 = api_client.post(
        "/task-dependencies",
        json={
            "depends_on_task_id": task_a.id,
            "dependent_task_id": task_b.id,
        },
        headers=auth_headers(db_session, owner.username),
    )
    assert response1.status_code == 201

    # Attempt to add B depends on A (would create 2-node cycle)
    response2 = api_client.post(
        "/task-dependencies",
        json={
            "depends_on_task_id": task_b.id,
            "dependent_task_id": task_a.id,
        },
        headers=auth_headers(db_session, owner.username),
    )
    assert response2.status_code == 400
    assert "cycle" in response2.json()["detail"].lower()

    # Verify dependency graph remains acyclic
    map_response = api_client.get(
        "/dependency-map",
        headers=auth_headers(db_session, owner.username),
    )
    assert map_response.status_code == 200
    dependency_map = map_response.json()
    assert len(dependency_map["edges"]) == 1  # Only A->B, not B->A


def test_create_dependency_rejects_cycle(api_client, db_session):
    """TC-DEP-02: Prevent Multi-node Cycles - Three tasks A, B, C exist."""
    owner = create_user(db_session, "owner", "owner@example.com")
    project = create_project(db_session, owner, name="CycleSafe")

    task_a = create_task(db_session, owner, project, title="Task A")
    task_b = create_task(db_session, owner, project, title="Task B")
    task_c = create_task(db_session, owner, project, title="Task C")

    create_dependency(db_session, owner, depends_on=task_a, dependent=task_b)
    create_dependency(db_session, owner, depends_on=task_b, dependent=task_c)

    # Attempt to add C depends on A (would create cycle A->B->C->A)
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
    
    # Verify existing edges unchanged
    map_response = api_client.get(
        "/dependency-map",
        headers=auth_headers(db_session, owner.username),
    )
    assert map_response.status_code == 200
    dependency_map = map_response.json()
    assert len(dependency_map["edges"]) == 2  # A->B and B->C, but not C->A


def test_create_dependency_rejects_self_loop(api_client, db_session):
    """TC-DEP-03: Prevent Self-loop Dependencies - A task exists."""
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
    """TC-DEP-05: Prevent Cross-project Dependencies - Tasks exist in different projects."""
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
    """TC-TASK-01: Task Status Transition Persists - Task exists with initial status."""
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
    """TC-SEC-02: Unauthenticated Requests Return 401 - User is not logged in."""
    response = api_client.get(path)
    assert response.status_code == 401


def test_horizontal_privilege_escalation_blocked(api_client, db_session):
    """TC-SEC-01: Horizontal Privilege Escalation Attempt - User A belongs to Project X only; Project Y exists."""
    owner = create_user(db_session, "alice", "alice@example.net")
    outsider = create_user(db_session, "mallory", "mallory@example.net")
    project = create_project(db_session, owner, name="Secrets", visibility="private")
    task = create_task(db_session, owner, project, title="Encrypt docs")

    # Outsider attempts to read task (via comments endpoint which checks task access)
    response = api_client.get(
        f"/tasks/{task.id}/comments",
        headers=auth_headers(db_session, outsider.username),
    )
    assert response.status_code in [403, 404]  # Forbidden or Not Found
    
    # Outsider attempts to update task
    response = api_client.patch(
        f"/tasks/{task.id}",
        json={"status": "completed"},
        headers=auth_headers(db_session, outsider.username),
    )
    assert response.status_code == 403
    
    # Outsider attempts to read project (via tasks endpoint which checks project access)
    response = api_client.get(
        f"/projects/{project.id}/tasks",
        headers=auth_headers(db_session, outsider.username),
    )
    assert response.status_code in [403, 404]
    
    # Verify no data leakage - project should not appear in outsider's project list
    projects_response = api_client.get(
        "/projects",
        headers=auth_headers(db_session, outsider.username),
    )
    assert projects_response.status_code == 200
    projects = projects_response.json()
    assert not any(p["id"] == project.id for p in projects)


def test_block_dependency_to_nonexistent_task(api_client, db_session):
    """TC-DEP-04: Block Dependency to Non-existent Task - A task A exists."""
    owner = create_user(db_session, "depowner", "depowner@example.com")
    project = create_project(db_session, owner, name="Dependency Project")
    task_a = create_task(db_session, owner, project, title="Task A")
    
    # Attempt to create dependency with non-existent depends_on task
    response = api_client.post(
        "/task-dependencies",
        json={
            "depends_on_task_id": 99999,  # Non-existent task
            "dependent_task_id": task_a.id,
        },
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code in [404, 400]  # Not found or bad request
    assert "not found" in response.json()["detail"].lower() or "invalid" in response.json()["detail"].lower()
    
    # Attempt to create dependency with non-existent dependent task
    response = api_client.post(
        "/task-dependencies",
        json={
            "depends_on_task_id": task_a.id,
            "dependent_task_id": 99999,  # Non-existent task
        },
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code in [404, 400]
    assert "not found" in response.json()["detail"].lower() or "invalid" in response.json()["detail"].lower()
    
    # Verify no dependency record was created
    map_response = api_client.get(
        "/dependency-map",
        headers=auth_headers(db_session, owner.username),
    )
    assert map_response.status_code == 200
    dependency_map = map_response.json()
    assert len(dependency_map["edges"]) == 0



def test_comment_mention_creates_notification(api_client, db_session):
    """TC-COM-01: Comment Mention Creates Notification - Task exists; target user is a project member."""
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
    """TC-SEC-03: Comment XSS Payload is Escaped - User attempts to inject script tags."""
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



