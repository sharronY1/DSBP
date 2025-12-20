"""Integration tests for Dependency Map functionality."""

from typing import Dict

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


def test_dependency_map_only_includes_accessible_projects(api_client, db_session):
    """test case: Dependency map only includes tasks from projects accessible to user"""
    owner = create_user(db_session, "map_owner", "map_owner@example.com")
    guest = create_user(db_session, "map_guest", "map_guest@example.com")
    
    # Owner's project with tasks
    owner_project = create_project(db_session, owner, name="Owner Project", visibility="private")
    owner_task1 = create_task(db_session, owner, owner_project, title="Owner Task 1")
    owner_task2 = create_task(db_session, owner, owner_project, title="Owner Task 2")
    create_dependency(db_session, owner, depends_on=owner_task1, dependent=owner_task2)
    
    # Guest's project with tasks
    guest_project = create_project(db_session, guest, name="Guest Project", visibility="private")
    guest_task1 = create_task(db_session, guest, guest_project, title="Guest Task 1")
    guest_task2 = create_task(db_session, guest, guest_project, title="Guest Task 2")
    create_dependency(db_session, guest, depends_on=guest_task1, dependent=guest_task2)
    
    # Owner should only see their own project's dependencies
    response = api_client.get(
        "/dependency-map",
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code == 200
    dependency_map = response.json()
    
    task_ids = {task["id"] for task in dependency_map["tasks"]}
    assert owner_task1.id in task_ids
    assert owner_task2.id in task_ids
    assert guest_task1.id not in task_ids
    assert guest_task2.id not in task_ids


def test_dependency_map_includes_multiple_projects(api_client, db_session):
    """test case: Dependency map includes dependencies from multiple accessible projects"""
    owner = create_user(db_session, "multi_map", "multi_map@example.com")
    
    # Project A
    project_a = create_project(db_session, owner, name="Project A")
    task_a1 = create_task(db_session, owner, project_a, title="A1")
    task_a2 = create_task(db_session, owner, project_a, title="A2")
    create_dependency(db_session, owner, depends_on=task_a1, dependent=task_a2)
    
    # Project B
    project_b = create_project(db_session, owner, name="Project B")
    task_b1 = create_task(db_session, owner, project_b, title="B1")
    task_b2 = create_task(db_session, owner, project_b, title="B2")
    create_dependency(db_session, owner, depends_on=task_b1, dependent=task_b2)
    
    response = api_client.get(
        "/dependency-map",
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code == 200
    dependency_map = response.json()
    
    # Verify all tasks are included
    task_ids = {task["id"] for task in dependency_map["tasks"]}
    assert len(task_ids) == 4
    assert task_a1.id in task_ids
    assert task_a2.id in task_ids
    assert task_b1.id in task_ids
    assert task_b2.id in task_ids
    
    # Verify edges from both projects
    assert len(dependency_map["edges"]) == 2


def test_dependency_map_edges_have_correct_structure(api_client, db_session):
    """test case: Dependency map edges have correct depends_on and dependent structure"""
    owner = create_user(db_session, "edge_owner", "edge_owner@example.com")
    project = create_project(db_session, owner, name="Edge Project")
    
    task1 = create_task(db_session, owner, project, title="Task 1")
    task2 = create_task(db_session, owner, project, title="Task 2")
    
    response = api_client.post(
        "/task-dependencies",
        json={
            "depends_on_task_id": task1.id,
            "dependent_task_id": task2.id,
        },
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code == 201
    
    # Get dependency map
    map_response = api_client.get(
        "/dependency-map",
        headers=auth_headers(db_session, owner.username),
    )
    assert map_response.status_code == 200
    dependency_map = map_response.json()
    
    # Verify edge structure
    assert len(dependency_map["edges"]) == 1
    edge = dependency_map["edges"][0]
    assert "id" in edge
    assert "depends_on" in edge
    assert "dependent" in edge
    assert edge["depends_on"]["id"] == task1.id
    assert edge["dependent"]["id"] == task2.id


def test_dependency_map_updates_after_deletion(api_client, db_session):
    """test case: Dependency map updates correctly after dependency deletion"""
    owner = create_user(db_session, "delete_map", "delete_map@example.com")
    project = create_project(db_session, owner, name="Delete Project")
    
    task1 = create_task(db_session, owner, project, title="Task 1")
    task2 = create_task(db_session, owner, project, title="Task 2")
    
    # Create dependency
    dep_response = api_client.post(
        "/task-dependencies",
        json={
            "depends_on_task_id": task1.id,
            "dependent_task_id": task2.id,
        },
        headers=auth_headers(db_session, owner.username),
    )
    assert dep_response.status_code == 201
    dependency_id = dep_response.json()["id"]
    
    # Verify dependency exists in map
    map_response = api_client.get(
        "/dependency-map",
        headers=auth_headers(db_session, owner.username),
    )
    assert map_response.status_code == 200
    dependency_map = map_response.json()
    assert len(dependency_map["edges"]) == 1
    
    # Delete dependency
    delete_response = api_client.delete(
        f"/task-dependencies/{dependency_id}",
        headers=auth_headers(db_session, owner.username),
    )
    assert delete_response.status_code == 204
    
    # Verify dependency removed from map
    map_response = api_client.get(
        "/dependency-map",
        headers=auth_headers(db_session, owner.username),
    )
    assert map_response.status_code == 200
    dependency_map = map_response.json()
    assert len(dependency_map["edges"]) == 0


def test_dependency_map_shared_project_includes_dependencies(api_client, db_session):
    """test case: Dependency map includes dependencies from shared projects"""
    owner = create_user(db_session, "share_owner", "share_owner@example.com")
    guest = create_user(db_session, "share_guest", "share_guest@example.com")
    
    # Owner creates project and shares with guest
    project = create_project(
        db_session,
        owner,
        name="Shared Project",
        visibility="selected",
        shared_usernames=[guest.username],
    )
    task1 = create_task(db_session, owner, project, title="Shared Task 1")
    task2 = create_task(db_session, owner, project, title="Shared Task 2")
    create_dependency(db_session, owner, depends_on=task1, dependent=task2)
    
    # Guest should see the dependency
    response = api_client.get(
        "/dependency-map",
        headers=auth_headers(db_session, guest.username),
    )
    assert response.status_code == 200
    dependency_map = response.json()
    
    task_ids = {task["id"] for task in dependency_map["tasks"]}
    assert task1.id in task_ids
    assert task2.id in task_ids
    assert len(dependency_map["edges"]) == 1
