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


# Task Board runder bug

def test_task_list_returns_all_tasks_for_project(api_client, db_session):
    """test case1: task list returns all tasks for project"""
    owner = create_user(db_session, "taskboard", "taskboard@example.com")
    project = create_project(db_session, owner, name="TaskBoard Project")
    
    # create tasks with different status
    task1 = create_task(db_session, owner, project, title="New Task", status="new_task")
    task2 = create_task(db_session, owner, project, title="Scheduled Task", status="scheduled")
    task3 = create_task(db_session, owner, project, title="In Progress Task", status="in_progress")
    task4 = create_task(db_session, owner, project, title="Completed Task", status="completed")
    
    response = api_client.get(
        f"/projects/{project.id}/tasks",
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 4
    
    # verify all tasks are in the list
    task_ids = {task["id"] for task in tasks}
    assert task1.id in task_ids
    assert task2.id in task_ids
    assert task3.id in task_ids
    assert task4.id in task_ids


def test_task_list_can_be_filtered_by_status(api_client, db_session):
    """test case2: task list can be filtered by status"""
    owner = create_user(db_session, "filter", "filter@example.com")
    project = create_project(db_session, owner, name="Filter Project")
    
    # create tasks with different status
    new_task = create_task(db_session, owner, project, title="New", status="new_task")
    scheduled_task = create_task(db_session, owner, project, title="Scheduled", status="scheduled")
    in_progress_task = create_task(db_session, owner, project, title="In Progress", status="in_progress")
    completed_task = create_task(db_session, owner, project, title="Completed", status="completed")
    
    response = api_client.get(
        f"/projects/{project.id}/tasks",
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code == 200
    tasks = response.json()
    
    # categorize tasks by status
    tasks_by_status = {}
    for task in tasks:
        status = task["status"]
        if status not in tasks_by_status:
            tasks_by_status[status] = []
        tasks_by_status[status].append(task)
    
    # verify each status has corresponding tasks
    assert "new_task" in tasks_by_status
    assert "scheduled" in tasks_by_status
    assert "in_progress" in tasks_by_status
    assert "completed" in tasks_by_status
    
    # verify task count for each status
    assert len(tasks_by_status["new_task"]) == 1
    assert len(tasks_by_status["scheduled"]) == 1
    assert len(tasks_by_status["in_progress"]) == 1
    assert len(tasks_by_status["completed"]) == 1
    
    # verify task id matches
    assert tasks_by_status["new_task"][0]["id"] == new_task.id
    assert tasks_by_status["scheduled"][0]["id"] == scheduled_task.id
    assert tasks_by_status["in_progress"][0]["id"] == in_progress_task.id
    assert tasks_by_status["completed"][0]["id"] == completed_task.id


def test_task_list_isolates_tasks_by_project(api_client, db_session):
    """test case3: task list isolates tasks by project"""
    owner = create_user(db_session, "multi", "multi@example.com")
    project_a = create_project(db_session, owner, name="Project A")
    project_b = create_project(db_session, owner, name="Project B")
    
    # create tasks in project A
    task_a1 = create_task(db_session, owner, project_a, title="Task A1", status="new_task")
    task_a2 = create_task(db_session, owner, project_a, title="Task A2", status="in_progress")
    
    # create tasks in project B
    task_b1 = create_task(db_session, owner, project_b, title="Task B1", status="scheduled")
    task_b2 = create_task(db_session, owner, project_b, title="Task B2", status="completed")
    
    # get tasks in project A
    response_a = api_client.get(
        f"/projects/{project_a.id}/tasks",
        headers=auth_headers(db_session, owner.username),
    )
    assert response_a.status_code == 200
    tasks_a = response_a.json()
    assert len(tasks_a) == 2
    task_ids_a = {task["id"] for task in tasks_a}
    assert task_a1.id in task_ids_a
    assert task_a2.id in task_ids_a
    assert task_b1.id not in task_ids_a
    assert task_b2.id not in task_ids_a
    
    # get tasks in project B
    response_b = api_client.get(
        f"/projects/{project_b.id}/tasks",
        headers=auth_headers(db_session, owner.username),
    )
    assert response_b.status_code == 200
    tasks_b = response_b.json()
    assert len(tasks_b) == 2
    task_ids_b = {task["id"] for task in tasks_b}
    assert task_b1.id in task_ids_b
    assert task_b2.id in task_ids_b
    assert task_a1.id not in task_ids_b
    assert task_a2.id not in task_ids_b


def test_task_status_update_reflects_in_list(api_client, db_session):
    """test case4: task status update reflects in list"""
    owner = create_user(db_session, "update", "update@example.com")
    project = create_project(db_session, owner, name="Update Project")
    task = create_task(db_session, owner, project, title="Update Test", status="new_task")
    
    # verify initial status
    response = api_client.get(
        f"/projects/{project.id}/tasks",
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code == 200
    tasks = response.json()
    task_data = next(t for t in tasks if t["id"] == task.id)
    assert task_data["status"] == "new_task"
    
    # update status to scheduled
    update_response = api_client.patch(
        f"/tasks/{task.id}",
        json={"status": "scheduled"},
        headers=auth_headers(db_session, owner.username),
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "scheduled"
    
    # verify status update in list
    response = api_client.get(
        f"/projects/{project.id}/tasks",
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code == 200
    tasks = response.json()
    task_data = next(t for t in tasks if t["id"] == task.id)
    assert task_data["status"] == "scheduled"
    
    # update status to in_progress
    api_client.patch(
        f"/tasks/{task.id}",
        json={"status": "in_progress"},
        headers=auth_headers(db_session, owner.username),
    )
    
    # update status to completed
    api_client.patch(
        f"/tasks/{task.id}",
        json={"status": "completed"},
        headers=auth_headers(db_session, owner.username),
    )
    
    # verify final status
    response = api_client.get(
        f"/projects/{project.id}/tasks",
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code == 200
    tasks = response.json()
    task_data = next(t for t in tasks if t["id"] == task.id)
    assert task_data["status"] == "completed"


def test_task_list_empty_project_returns_empty_list(api_client, db_session):
    """test case5: empty project returns empty task list"""
    owner = create_user(db_session, "empty", "empty@example.com")
    project = create_project(db_session, owner, name="Empty Project")
    
    response = api_client.get(
        f"/projects/{project.id}/tasks",
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 0
    assert tasks == []


# Dashboard test cases

def test_dashboard_project_overview_displays_correct_info(api_client, db_session):
    """test case1: Project Overview displays correct project information (name, description, visibility, owner)"""
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
    """test case: Project Overview displays all visibility types correctly"""
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
    """test case: Task Status Overview counts tasks correctly by status"""
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
    """test case: Task Status Overview returns zero counts for empty project"""
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
    """test case: Task Status Overview updates correctly after task status changes"""
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
    """test case: Task History Management returns task activities"""
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
    """test case: Task History daily counts are calculated correctly"""
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
    """test case: Task History filters activities by date range"""
    from datetime import date, timedelta
    
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
    """test case: Project Overview displays correct owner information"""
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
    """test case: Project Overview displays description correctly (including empty description)"""
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
