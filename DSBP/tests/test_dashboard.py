"""Integration tests for Dashboard functionality."""

from typing import Dict

from tests.factories import (
    create_project,
    create_task,
    create_user,
    login_user,
)


def auth_headers(db_session, username: str, password: str = "secret123") -> Dict[str, str]:
    token = login_user(db_session, username, password)
    return {"Authorization": f"Bearer {token}"}


def test_dashboard_project_overview_displays_correct_info(api_client, db_session):
    """TC-DASH-01: Project Overview Displays Correct Info - Project exists with all fields."""
    owner = create_user(db_session, "dashboard_owner", "dashboard_owner@example.com")
    project = create_project(
        db_session,
        owner,
        name="Dashboard Test Project",
        description="This is a test project for dashboard",
        visibility="selected",
    )
    
    # Get project list to verify project info
    response = api_client.get(
        "/projects",
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code == 200
    projects = response.json()
    
    # Find the project
    project_data = next((p for p in projects if p["id"] == project.id), None)
    assert project_data is not None
    
    # Verify project overview fields
    assert project_data["name"] == "Dashboard Test Project"
    assert project_data["description"] == "This is a test project for dashboard"
    assert project_data["visibility"] == "selected"
    assert project_data["owner_id"] == owner.id


def test_dashboard_project_overview_displays_all_visibility_types(api_client, db_session):
    """TC-DASH-02: Project Overview Displays All Visibility Types - Projects with different visibility exist."""
    owner = create_user(db_session, "visibility_owner", "visibility_owner@example.com")
    
    # Create projects with different visibility settings
    project_all = create_project(db_session, owner, name="Public Project", visibility="all")
    project_private = create_project(db_session, owner, name="Private Project", visibility="private")
    project_selected = create_project(db_session, owner, name="Selected Project", visibility="selected")
    
    response = api_client.get(
        "/projects",
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code == 200
    projects = response.json()
    
    # Verify visibility values
    project_dict = {p["id"]: p for p in projects}
    assert project_dict[project_all.id]["visibility"] == "all"
    assert project_dict[project_private.id]["visibility"] == "private"
    assert project_dict[project_selected.id]["visibility"] == "selected"


def test_dashboard_task_status_overview_counts_tasks_correctly(api_client, db_session):
    """TC-DASH-03: Task Status Overview Counts Tasks Correctly - Project has tasks with different statuses."""
    owner = create_user(db_session, "status_owner", "status_owner@example.com")
    project = create_project(db_session, owner, name="Status Project")
    
    # Create tasks with different statuses
    create_task(db_session, owner, project, title="Task 1", status="new_task")
    create_task(db_session, owner, project, title="Task 2", status="new_task")
    create_task(db_session, owner, project, title="Task 3", status="scheduled")
    create_task(db_session, owner, project, title="Task 4", status="in_progress")
    create_task(db_session, owner, project, title="Task 5", status="in_progress")
    create_task(db_session, owner, project, title="Task 6", status="completed")
    
    response = api_client.get(
        f"/projects/{project.id}/dashboard",
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code == 200
    dashboard_data = response.json()
    
    # Verify dashboard response structure
    assert dashboard_data["project_id"] == project.id
    assert dashboard_data["total_tasks"] == 6
    assert "status_counts" in dashboard_data
    assert "updated_at" in dashboard_data
    
    # Verify status counts
    status_counts = dashboard_data["status_counts"]
    assert status_counts["new_task"] == 2
    assert status_counts["scheduled"] == 1
    assert status_counts["in_progress"] == 2
    assert status_counts["completed"] == 1


def test_dashboard_task_status_overview_empty_project(api_client, db_session):
    """TC-DASH-04: Task Status Overview Empty Project - Project exists with no tasks."""
    owner = create_user(db_session, "empty_dash", "empty_dash@example.com")
    project = create_project(db_session, owner, name="Empty Dashboard Project")
    
    response = api_client.get(
        f"/projects/{project.id}/dashboard",
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code == 200
    dashboard_data = response.json()
    
    assert dashboard_data["project_id"] == project.id
    assert dashboard_data["total_tasks"] == 0
    assert dashboard_data["status_counts"] == {}


def test_dashboard_task_status_overview_updates_after_status_change(api_client, db_session):
    """TC-DASH-05: Task Status Overview Updates After Status Change - Task exists with initial status."""
    owner = create_user(db_session, "update_dash", "update_dash@example.com")
    project = create_project(db_session, owner, name="Update Dashboard Project")
    task = create_task(db_session, owner, project, title="Status Change Task", status="new_task")
    
    # Initial dashboard check
    response = api_client.get(
        f"/projects/{project.id}/dashboard",
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code == 200
    dashboard_data = response.json()
    assert dashboard_data["status_counts"]["new_task"] == 1
    assert dashboard_data["total_tasks"] == 1
    
    # Update task status to scheduled
    api_client.patch(
        f"/tasks/{task.id}",
        json={"status": "scheduled"},
        headers=auth_headers(db_session, owner.username),
    )
    
    # Check dashboard after status change
    response = api_client.get(
        f"/projects/{project.id}/dashboard",
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code == 200
    dashboard_data = response.json()
    assert "new_task" not in dashboard_data["status_counts"] or dashboard_data["status_counts"].get("new_task", 0) == 0
    assert dashboard_data["status_counts"]["scheduled"] == 1
    assert dashboard_data["total_tasks"] == 1


def test_dashboard_task_history_returns_activities(api_client, db_session):
    """TC-DASH-06: Task History Returns Activities - Project has tasks with activity history."""
    owner = create_user(db_session, "history_owner", "history_owner@example.com")
    project = create_project(db_session, owner, name="History Project")
    
    # Create tasks to generate activities
    task1 = create_task(db_session, owner, project, title="History Task 1")
    task2 = create_task(db_session, owner, project, title="History Task 2")
    
    response = api_client.get(
        f"/projects/{project.id}/task-history",
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code == 200
    history_data = response.json()
    
    # Verify history response structure
    assert "activities" in history_data
    assert "daily_counts" in history_data
    
    # Verify activities exist (at least 2 for the 2 tasks created)
    assert len(history_data["activities"]) >= 2
    
    # Verify daily_counts structure
    assert isinstance(history_data["daily_counts"], dict)


def test_dashboard_task_history_daily_counts_are_correct(api_client, db_session):
    """TC-DASH-07: Task History Daily Counts Are Correct - Project has multiple tasks created."""
    owner = create_user(db_session, "counts_owner", "counts_owner@example.com")
    project = create_project(db_session, owner, name="Counts Project")
    
    # Create multiple tasks
    create_task(db_session, owner, project, title="Task 1")
    create_task(db_session, owner, project, title="Task 2")
    create_task(db_session, owner, project, title="Task 3")
    
    response = api_client.get(
        f"/projects/{project.id}/task-history",
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code == 200
    history_data = response.json()
    
    # Verify daily_counts has entries
    assert len(history_data["daily_counts"]) > 0
    
    # Verify total activities match sum of daily counts
    total_from_counts = sum(history_data["daily_counts"].values())
    assert total_from_counts == len(history_data["activities"])


def test_dashboard_task_history_filters_by_date_range(api_client, db_session):
    """TC-DASH-08: Task History Filters by Date Range - Project has tasks with activity history."""
    from datetime import date
    
    owner = create_user(db_session, "filter_owner", "filter_owner@example.com")
    project = create_project(db_session, owner, name="Filter Project")
    
    # Create tasks
    create_task(db_session, owner, project, title="Task 1")
    create_task(db_session, owner, project, title="Task 2")
    
    # Get history with date filter (today)
    today = date.today()
    response = api_client.get(
        f"/projects/{project.id}/task-history",
        params={"date_filter": today.isoformat()},
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code == 200
    history_data = response.json()
    
    # Verify response structure
    assert "activities" in history_data
    assert "daily_counts" in history_data
    
    # Verify activities are filtered (should only include today's activities)
    today_str = today.isoformat()
    if today_str in history_data["daily_counts"]:
        assert history_data["daily_counts"][today_str] > 0


def test_dashboard_project_overview_owner_display(api_client, db_session):
    """TC-DASH-09: Project Overview Owner Display - Multiple projects with different owners exist."""
    owner1 = create_user(db_session, "owner1", "owner1@example.com")
    owner2 = create_user(db_session, "owner2", "owner2@example.com")
    
    project1 = create_project(db_session, owner1, name="Owner1 Project")
    project2 = create_project(db_session, owner2, name="Owner2 Project")
    
    # Check owner1's projects
    response = api_client.get(
        "/projects",
        headers=auth_headers(db_session, owner1.username),
    )
    assert response.status_code == 200
    projects = response.json()
    
    project_dict = {p["id"]: p for p in projects}
    assert project_dict[project1.id]["owner_id"] == owner1.id
    assert project_dict[project2.id]["owner_id"] == owner2.id
    
    # Verify owner names are accessible via user list
    users_response = api_client.get(
        "/users",
        headers=auth_headers(db_session, owner1.username),
    )
    assert users_response.status_code == 200
    users = users_response.json()
    user_dict = {u["id"]: u for u in users}
    assert user_dict[owner1.id]["username"] == "owner1"
    assert user_dict[owner2.id]["username"] == "owner2"


def test_dashboard_project_overview_description_display(api_client, db_session):
    """TC-DASH-10: Project Overview Description Display - Projects with and without descriptions exist."""
    owner = create_user(db_session, "desc_owner", "desc_owner@example.com")
    
    # Project with description
    project_with_desc = create_project(
        db_session,
        owner,
        name="With Description",
        description="This project has a description",
    )
    
    # Project without description
    project_no_desc = create_project(
        db_session,
        owner,
        name="No Description",
        description="",
    )
    
    response = api_client.get(
        "/projects",
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code == 200
    projects = response.json()
    
    project_dict = {p["id"]: p for p in projects}
    assert project_dict[project_with_desc.id]["description"] == "This project has a description"
    assert project_dict[project_no_desc.id]["description"] == ""
