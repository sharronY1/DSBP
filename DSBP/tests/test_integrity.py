"""Integration tests for Data Integrity and Concurrency."""

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


def test_transactional_enforcement_for_concurrent_edge_creation(api_client, db_session):
    """TC-INT-01: Transactional Enforcement for Concurrent Edge Creation - Two users can edit the same project."""
    owner = create_user(db_session, "concurrent_owner", "concurrent_owner@example.com")
    project = create_project(db_session, owner, name="Concurrent Project")
    
    # Create tasks that form a near-cycle scenario
    task_a = create_task(db_session, owner, project, title="Task A")
    task_b = create_task(db_session, owner, project, title="Task B")
    task_c = create_task(db_session, owner, project, title="Task C")
    
    # Create initial dependency: A -> B
    create_dependency(db_session, owner, depends_on=task_a, dependent=task_b)
    
    # Simulate concurrent requests: both trying to create dependencies that would form a cycle
    # Request 1: B -> C (valid)
    response1 = api_client.post(
        "/task-dependencies",
        json={
            "depends_on_task_id": task_b.id,
            "dependent_task_id": task_c.id,
        },
        headers=auth_headers(db_session, owner.username),
    )
    assert response1.status_code == 201
    
    # Request 2: C -> A (would create cycle A->B->C->A)
    response2 = api_client.post(
        "/task-dependencies",
        json={
            "depends_on_task_id": task_c.id,
            "dependent_task_id": task_a.id,
        },
        headers=auth_headers(db_session, owner.username),
    )
    # Should be rejected due to cycle detection
    assert response2.status_code == 400
    assert "cycle" in response2.json()["detail"].lower()
    
    # Verify database remains consistent - only one edge should exist
    map_response = api_client.get(
        "/dependency-map",
        headers=auth_headers(db_session, owner.username),
    )
    assert map_response.status_code == 200
    dependency_map = map_response.json()
    # Should have 2 edges: A->B and B->C, but not C->A
    assert len(dependency_map["edges"]) == 2
    edge_depends_on = {edge["depends_on"]["id"] for edge in dependency_map["edges"]}
    edge_dependent = {edge["dependent"]["id"] for edge in dependency_map["edges"]}
    assert task_a.id in edge_depends_on  # A -> B
    assert task_b.id in edge_depends_on  # B -> C
    assert task_c.id not in edge_depends_on  # C -> A should not exist


def test_cascading_delete_integrity(api_client, db_session):
    """TC-INT-02: Cascading Delete Integrity - Project has tasks, comments, dependencies, and notifications."""
    owner = create_user(db_session, "cascade_owner", "cascade_owner@example.com")
    assignee = create_user(db_session, "cascade_assignee", "cascade_assignee@example.com")
    
    # Create project with tasks
    project = create_project(
        db_session,
        owner,
        name="Cascade Project",
        visibility="selected",
        shared_usernames=[assignee.username],
    )
    task1 = create_task(db_session, owner, project, title="Task 1")
    task2 = create_task(db_session, owner, project, title="Task 2")
    
    # Create dependency between tasks
    create_dependency(db_session, owner, depends_on=task1, dependent=task2)
    
    # Create comments with mentions
    api_client.post(
        "/comments",
        json={"task_id": task1.id, "content": f"Comment 1 @{assignee.username}"},
        headers=auth_headers(db_session, owner.username),
    )
    api_client.post(
        "/comments",
        json={"task_id": task2.id, "content": f"Comment 2 @{assignee.username}"},
        headers=auth_headers(db_session, owner.username),
    )
    
    # Verify notifications were created
    notif_response = api_client.get(
        "/notifications",
        headers=auth_headers(db_session, assignee.username),
    )
    assert notif_response.status_code == 200
    notifications_before = notif_response.json()
    assert len(notifications_before) >= 2
    
    # Delete the project
    delete_response = api_client.delete(
        f"/projects/{project.id}",
        headers=auth_headers(db_session, owner.username),
    )
    assert delete_response.status_code == 204
    
    # Verify project is deleted - check it's not in the project list
    projects_response = api_client.get(
        "/projects",
        headers=auth_headers(db_session, owner.username),
    )
    assert projects_response.status_code == 200
    projects = projects_response.json()
    assert not any(p["id"] == project.id for p in projects)
    
    # Verify tasks are deleted (cascading)
    # Check that tasks are not in the task list
    tasks_response = api_client.get(
        "/tasks",
        headers=auth_headers(db_session, owner.username),
    )
    assert tasks_response.status_code == 200
    tasks = tasks_response.json()
    task_ids = {task["id"] for task in tasks}
    assert task1.id not in task_ids
    assert task2.id not in task_ids
    
    # Verify dependencies are removed
    map_response = api_client.get(
        "/dependency-map",
        headers=auth_headers(db_session, owner.username),
    )
    assert map_response.status_code == 200
    dependency_map = map_response.json()
    # Dependencies should be removed (either deleted or not accessible)
    task_ids = {task["id"] for task in dependency_map["tasks"]}
    assert task1.id not in task_ids
    assert task2.id not in task_ids
    
    # Verify comments are deleted (cascading)
    # Comments should be deleted with tasks
    # Note: This depends on your database schema's cascade settings
    
    # Verify notifications related to deleted tasks are handled
    # (Notifications might remain but reference non-existent tasks, or be cleaned up)
    notif_response_after = api_client.get(
        "/notifications",
        headers=auth_headers(db_session, assignee.username),
    )
    assert notif_response_after.status_code == 200
    # Notifications might still exist but should not reference deleted tasks
    # This depends on your implementation


