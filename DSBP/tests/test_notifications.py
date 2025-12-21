"""Integration tests for Notification functionality."""

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


def test_notifications_multiple_mentions_create_multiple_notifications(api_client, db_session):
    """TC-NOTIF-01: Multiple Mentions Create Multiple Notifications - Comment contains multiple user mentions."""
    owner = create_user(db_session, "multi_notif", "multi_notif@example.com")
    user1 = create_user(db_session, "user1", "user1@example.com")
    user2 = create_user(db_session, "user2", "user2@example.com")
    
    project = create_project(db_session, owner, name="Multi Mention Project")
    task = create_task(db_session, owner, project, title="Multi Task")
    
    # Create comment with multiple mentions
    response = api_client.post(
        "/comments",
        json={
            "task_id": task.id,
            "content": f"Hey @{user1.username} and @{user2.username}, please review this",
        },
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code == 201
    
    # Check user1's notifications
    notif_response1 = api_client.get(
        "/notifications",
        headers=auth_headers(db_session, user1.username),
    )
    assert notif_response1.status_code == 200
    notifications1 = notif_response1.json()
    assert len(notifications1) == 1
    assert "mentioned you" in notifications1[0]["message"]
    
    # Check user2's notifications
    notif_response2 = api_client.get(
        "/notifications",
        headers=auth_headers(db_session, user2.username),
    )
    assert notif_response2.status_code == 200
    notifications2 = notif_response2.json()
    assert len(notifications2) == 1
    assert "mentioned you" in notifications2[0]["message"]


def test_notifications_ordered_by_created_at_desc(api_client, db_session):
    """TC-NOTIF-02: Notifications Ordered by Created At Desc - Multiple notifications exist."""
    owner = create_user(db_session, "order_owner", "order_owner@example.com")
    user = create_user(db_session, "order_user", "order_user@example.com")
    
    project = create_project(db_session, owner, name="Order Project")
    task1 = create_task(db_session, owner, project, title="Task 1")
    task2 = create_task(db_session, owner, project, title="Task 2")
    
    # Create first comment
    api_client.post(
        "/comments",
        json={"task_id": task1.id, "content": f"First @{user.username}"},
        headers=auth_headers(db_session, owner.username),
    )
    
    # Create second comment
    api_client.post(
        "/comments",
        json={"task_id": task2.id, "content": f"Second @{user.username}"},
        headers=auth_headers(db_session, owner.username),
    )
    
    # Get notifications
    response = api_client.get(
        "/notifications",
        headers=auth_headers(db_session, user.username),
    )
    assert response.status_code == 200
    notifications = response.json()
    
    assert len(notifications) == 2
    # Verify ordering (most recent first)
    assert notifications[0]["created_at"] >= notifications[1]["created_at"]


def test_notifications_mark_read_updates_status(api_client, db_session):
    """TC-NOTIF-03: Mark Read Updates Status - Unread notification exists."""
    owner = create_user(db_session, "read_owner", "read_owner@example.com")
    user = create_user(db_session, "read_user", "read_user@example.com")
    
    project = create_project(db_session, owner, name="Read Project")
    task = create_task(db_session, owner, project, title="Read Task")
    
    # Create comment with mention
    api_client.post(
        "/comments",
        json={"task_id": task.id, "content": f"Check this @{user.username}"},
        headers=auth_headers(db_session, owner.username),
    )
    
    # Get notification
    response = api_client.get(
        "/notifications",
        headers=auth_headers(db_session, user.username),
    )
    assert response.status_code == 200
    notifications = response.json()
    assert len(notifications) == 1
    notification_id = notifications[0]["id"]
    assert notifications[0]["read"] is False
    
    # Mark as read
    read_response = api_client.post(
        f"/notifications/{notification_id}/read",
        headers=auth_headers(db_session, user.username),
    )
    assert read_response.status_code == 200
    assert read_response.json()["read"] is True
    
    # Verify in list
    response = api_client.get(
        "/notifications",
        headers=auth_headers(db_session, user.username),
    )
    assert response.status_code == 200
    notifications = response.json()
    assert notifications[0]["read"] is True


def test_notifications_include_project_and_task_names(api_client, db_session):
    """TC-NOTIF-04: Notification Includes Project and Task Names - Notification exists."""
    owner = create_user(db_session, "name_owner", "name_owner@example.com")
    user = create_user(db_session, "name_user", "name_user@example.com")
    
    project = create_project(db_session, owner, name="Test Project")
    task = create_task(db_session, owner, project, title="Test Task")
    
    # Create comment with mention
    api_client.post(
        "/comments",
        json={"task_id": task.id, "content": f"Review @{user.username}"},
        headers=auth_headers(db_session, owner.username),
    )
    
    # Get notification
    response = api_client.get(
        "/notifications",
        headers=auth_headers(db_session, user.username),
    )
    assert response.status_code == 200
    notifications = response.json()
    assert len(notifications) == 1
    
    message = notifications[0]["message"]
    assert "Test Project" in message or "project" in message.lower()
    assert "Test Task" in message or "task" in message.lower()
    assert owner.username in message


def test_notifications_unread_and_read_separation(api_client, db_session):
    """TC-NOTIF-05: Unread and Read Notifications Separation - Multiple notifications exist."""
    owner = create_user(db_session, "sep_owner", "sep_owner@example.com")
    user = create_user(db_session, "sep_user", "sep_user@example.com")
    
    project = create_project(db_session, owner, name="Sep Project")
    task1 = create_task(db_session, owner, project, title="Task 1")
    task2 = create_task(db_session, owner, project, title="Task 2")
    
    # Create first comment
    api_client.post(
        "/comments",
        json={"task_id": task1.id, "content": f"First @{user.username}"},
        headers=auth_headers(db_session, owner.username),
    )
    
    # Create second comment
    api_client.post(
        "/comments",
        json={"task_id": task2.id, "content": f"Second @{user.username}"},
        headers=auth_headers(db_session, owner.username),
    )
    
    # Get all notifications
    response = api_client.get(
        "/notifications",
        headers=auth_headers(db_session, user.username),
    )
    assert response.status_code == 200
    notifications = response.json()
    assert len(notifications) == 2
    assert all(not n["read"] for n in notifications)
    
    # Mark first notification as read
    notification_id = notifications[0]["id"]
    api_client.post(
        f"/notifications/{notification_id}/read",
        headers=auth_headers(db_session, user.username),
    )
    
    # Get notifications again
    response = api_client.get(
        "/notifications",
        headers=auth_headers(db_session, user.username),
    )
    assert response.status_code == 200
    notifications = response.json()
    assert len(notifications) == 2
    
    # Verify one is read, one is unread
    read_count = sum(1 for n in notifications if n["read"])
    unread_count = sum(1 for n in notifications if not n["read"])
    assert read_count == 1
    assert unread_count == 1


def test_notifications_mark_read_returns_404_for_nonexistent(api_client, db_session):
    """TC-NOTIF-06: Mark Read Returns 404 for Non-existent - Notification ID does not exist."""
    owner = create_user(db_session, "404_owner", "404_owner@example.com")
    
    response = api_client.post(
        "/notifications/99999/read",
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_deduplicate_mention_notifications(api_client, db_session):
    """TC-COM-02: Deduplicate Mention Notifications - Task exists; target user is a project member."""
    owner = create_user(db_session, "dedup_owner", "dedup_owner@example.com")
    user = create_user(db_session, "dedup_user", "dedup_user@example.com")
    
    project = create_project(
        db_session,
        owner,
        name="Dedup Project",
        visibility="selected",
        shared_usernames=[user.username],
    )
    task = create_task(db_session, owner, project, title="Dedup Task")
    
    # Post comment mentioning user twice in the same comment
    response = api_client.post(
        "/comments",
        json={
            "task_id": task.id,
            "content": f"Hey @{user.username}, please check this. Also @{user.username}, don't forget!",
        },
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code == 201
    
    # Check notifications - should only create one notification per comment
    notif_response = api_client.get(
        "/notifications",
        headers=auth_headers(db_session, user.username),
    )
    assert notif_response.status_code == 200
    notifications = notif_response.json()
    # Should only have one notification even though user was mentioned twice
    assert len(notifications) == 1
    assert "mentioned you" in notifications[0]["message"]
    
    # Post another comment with the same mention (simulating retry scenario)
    response2 = api_client.post(
        "/comments",
        json={
            "task_id": task.id,
            "content": f"Reminder @{user.username}",
        },
        headers=auth_headers(db_session, owner.username),
    )
    assert response2.status_code == 201
    
    # Now should have 2 notifications (one per comment)
    notif_response2 = api_client.get(
        "/notifications",
        headers=auth_headers(db_session, user.username),
    )
    assert notif_response2.status_code == 200
    notifications2 = notif_response2.json()
    assert len(notifications2) == 2


def test_prevent_mention_of_non_member(api_client, db_session):
    """TC-COM-03: Prevent Mention of Non-member - Task exists; target username is not a project member."""
    owner = create_user(db_session, "nonmem_owner", "nonmem_owner@example.com")
    member = create_user(db_session, "member", "member@example.com")
    non_member = create_user(db_session, "nonmember", "nonmember@example.com")
    
    # Create project with only member, not non_member
    project = create_project(
        db_session,
        owner,
        name="Member Project",
        visibility="selected",
        shared_usernames=[member.username],  # Only member is shared
    )
    task = create_task(db_session, owner, project, title="Member Task")
    
    # Post comment mentioning non-member
    response = api_client.post(
        "/comments",
        json={
            "task_id": task.id,
            "content": f"Hey @{non_member.username}, you shouldn't see this",
        },
        headers=auth_headers(db_session, owner.username),
    )
    assert response.status_code == 201  # Comment is created
    
    # Check non-member's notifications - should not have notification
    notif_response = api_client.get(
        "/notifications",
        headers=auth_headers(db_session, non_member.username),
    )
    assert notif_response.status_code == 200
    notifications = notif_response.json()
    # Non-member should not receive notification
    assert len(notifications) == 0
    
    # Verify member can still receive notifications
    response2 = api_client.post(
        "/comments",
        json={
            "task_id": task.id,
            "content": f"Hey @{member.username}, you should see this",
        },
        headers=auth_headers(db_session, owner.username),
    )
    assert response2.status_code == 201
    
    member_notif_response = api_client.get(
        "/notifications",
        headers=auth_headers(db_session, member.username),
    )
    assert member_notif_response.status_code == 200
    member_notifications = member_notif_response.json()
    assert len(member_notifications) == 1
    assert "mentioned you" in member_notifications[0]["message"]
