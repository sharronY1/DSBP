"""Integration tests for Authentication functionality."""

from datetime import timedelta
from typing import Dict

import pytest

from app.services import auth
from tests.factories import (
    create_project,
    create_task,
    create_user,
    login_user,
)


def auth_headers(db_session, username: str, password: str = "secret123") -> Dict[str, str]:
    token = login_user(db_session, username, password)
    return {"Authorization": f"Bearer {token}"}


def test_login_success_path(api_client, db_session):
    """TC-AUTH-01: Login (Success Path) - Valid user account exists; backend is reachable."""
    # Create a valid user
    user = create_user(db_session, "testuser", "testuser@example.com", password="secret123")
    
    # Attempt login with valid credentials
    response = api_client.post(
        "/auth/login",
        json={"username": "testuser", "password": "secret123"},
    )
    
    # Verify successful login
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0
    
    # Verify token can be used to access protected endpoint
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    me_response = api_client.get("/users/me", headers=headers)
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["username"] == "testuser"
    assert me_data["email"] == "testuser@example.com"


def test_login_invalid_password(api_client, db_session):
    """TC-AUTH-02: Login (Invalid Password) - Valid email exists."""
    # Create a valid user
    create_user(db_session, "testuser2", "testuser2@example.com", password="correctpass")
    
    # Attempt login with wrong password
    response = api_client.post(
        "/auth/login",
        json={"username": "testuser2", "password": "wrongpassword"},
    )
    
    # Verify login is rejected
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]
    
    # Verify no token is returned
    assert "access_token" not in response.json()


def test_session_expiration_handling(api_client, db_session):
    """TC-AUTH-03: Session Expiration Handling - User logged in; token is expired or invalidated."""
    # Create user and get a token
    user = create_user(db_session, "expireuser", "expireuser@example.com", password="secret123")
    token = login_user(db_session, "expireuser", "secret123")
    
    # Create a project to test with
    project = create_project(db_session, user, name="Test Project")
    
    # Verify token works initially
    headers = {"Authorization": f"Bearer {token}"}
    response = api_client.get("/projects", headers=headers)
    assert response.status_code == 200
    
    # Create an expired token (by creating one with very short expiration)
    expired_token = auth.create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(seconds=-1)  # Already expired
    )
    
    # Attempt to use expired token
    expired_headers = {"Authorization": f"Bearer {expired_token}"}
    expired_response = api_client.get("/projects", headers=expired_headers)
    
    # Verify API returns 401 for expired token
    assert expired_response.status_code == 401
    
    # Test with invalid token format
    invalid_headers = {"Authorization": "Bearer invalid_token_here"}
    invalid_response = api_client.get("/projects", headers=invalid_headers)
    assert invalid_response.status_code == 401
    
    # Test with missing token
    no_token_response = api_client.get("/projects")
    assert no_token_response.status_code == 401

