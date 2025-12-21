"""Integration tests for Task Board functionality."""

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


def test_task_list_returns_all_tasks_for_project(api_client, db_session):
    """TC-TASK-02: Task List Returns All Tasks for Project - Project exists with multiple tasks."""
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
    """TC-TASK-03: Task List Can Be Filtered by Status - Project has tasks with different statuses."""
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
    """TC-TASK-04: Task List Isolates Tasks by Project - Multiple projects exist with tasks."""
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
    """TC-TASK-05: Task Status Update Reflects in List - Task exists with initial status."""
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
    """TC-TASK-06: Empty Project Returns Empty Task List - Project exists with no tasks."""
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


def test_create_project_and_add_task(api_client, db_session):
    """TC-PT-01: Create Project and Add Task - User is logged in."""
    from datetime import date
    
    owner = create_user(db_session, "creator", "creator@example.com")
    
    # Create a project
    project_response = api_client.post(
        "/projects",
        json={
            "name": "New Project",
            "description": "Test project creation",
            "visibility": "private",
        },
        headers=auth_headers(db_session, owner.username),
    )
    assert project_response.status_code == 201
    project_data = project_response.json()
    project_id = project_data["id"]
    
    # Verify project appears in list
    projects_response = api_client.get(
        "/projects",
        headers=auth_headers(db_session, owner.username),
    )
    assert projects_response.status_code == 200
    projects = projects_response.json()
    assert any(p["id"] == project_id for p in projects)
    
    # Add a task with title, assignee, and due date
    assignee = create_user(db_session, "assignee", "assignee@example.com")
    due_date = date.today()
    
    task_response = api_client.post(
        "/tasks",
        json={
            "project_id": project_id,
            "title": "New Task",
            "description": "Task description",
            "status": "new_task",
            "due_date": due_date.isoformat(),
            "assignee_ids": [assignee.id],
        },
        headers=auth_headers(db_session, owner.username),
    )
    assert task_response.status_code == 201
    task_data = task_response.json()
    assert task_data["title"] == "New Task"
    assert task_data["project_id"] == project_id
    # Compare only date part (YYYY-MM-DD), ignoring time component
    returned_due_date = task_data["due_date"]
    if "T" in returned_due_date:
        returned_due_date = returned_due_date.split("T")[0]
    assert returned_due_date == due_date.isoformat()
    assert len(task_data["assignees"]) == 1
    assert task_data["assignees"][0]["id"] == assignee.id
    
    # Verify task appears in project task list
    tasks_response = api_client.get(
        f"/projects/{project_id}/tasks",
        headers=auth_headers(db_session, owner.username),
    )
    assert tasks_response.status_code == 200
    tasks = tasks_response.json()
    assert any(t["id"] == task_data["id"] for t in tasks)


def test_reject_invalid_task_payload(api_client, db_session):
    """TC-PT-03: Reject Invalid Task Payload - User is logged in."""
    from datetime import date
    
    owner = create_user(db_session, "validator", "validator@example.com")
    project = create_project(db_session, owner, name="Validation Project")
    
    # Test empty title
    response = api_client.post(
        "/tasks",
        json={
            "project_id": project.id,
            "title": "",  # Empty title
            "status": "new_task",
        },
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code == 422  # Validation error
    
    # Test invalid due date format
    response = api_client.post(
        "/tasks",
        json={
            "project_id": project.id,
            "title": "Valid Title",
            "status": "new_task",
            "due_date": "invalid-date-format",  # Invalid format
        },
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code == 422  # Validation error
    
    # Test invalid status
    response = api_client.post(
        "/tasks",
        json={
            "project_id": project.id,
            "title": "Valid Title",
            "status": "invalid_status",  # Invalid status
        },
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code == 422  # Validation error
    
    # Test non-existent project_id
    response = api_client.post(
        "/tasks",
        json={
            "project_id": 99999,  # Non-existent project
            "title": "Valid Title",
            "status": "new_task",
        },
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code in [404, 403]  # Not found or forbidden
    
    # Verify no partial records were created
    tasks_response = api_client.get(
        f"/projects/{project.id}/tasks",
        headers=auth_headers(db_session, owner.username),
    )
    assert tasks_response.status_code == 200
    tasks = tasks_response.json()
    assert len(tasks) == 0  # No tasks should have been created
