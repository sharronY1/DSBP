"""Integration tests for License management functionality."""

import pytest
from sqlalchemy.orm import Session

import app.models as models
from app.services import license as license_service
from tests.factories import create_user, login_user


def test_validate_license_key_format():
    """TC-LICENSE-01: Validate license key format validation"""
    # Valid formats
    assert license_service.validate_license_key_format("AAAA-BBBB-CCCC-DDDD") == True
    assert license_service.validate_license_key_format("1234-5678-ABCD-EFGH") == True
    assert license_service.validate_license_key_format("TEST-0000-0000-0001") == True
    
    # Invalid formats
    assert license_service.validate_license_key_format("AAAA-BBBB-CCCC") == False  # Too short
    assert license_service.validate_license_key_format("AAAA-BBBB-CCCC-DDDD-EEEE") == False  # Too long
    assert license_service.validate_license_key_format("AAAA BBBB CCCC DDDD") == False  # Spaces
    # Note: lowercase will be normalized, so validation converts to uppercase first, making lowercase format valid
    assert license_service.validate_license_key_format("aaaa-bbbb-cccc-dddd") == True  # Lowercase will be normalized
    assert license_service.validate_license_key_format("") == False  # Empty string
    assert license_service.validate_license_key_format("INVALID") == False  # Invalid format


def test_normalize_license_key():
    """TC-LICENSE-02: Validate license key normalization"""
    assert license_service.normalize_license_key("aaaa-bbbb-cccc-dddd") == "AAAA-BBBB-CCCC-DDDD"
    assert license_service.normalize_license_key("  AAAA-BBBB-CCCC-DDDD  ") == "AAAA-BBBB-CCCC-DDDD"
    assert license_service.normalize_license_key("Test-1234-5678-AbCd") == "TEST-1234-5678-ABCD"


def test_parse_license_file():
    """TC-LICENSE-03: Validate license file parsing"""
    file_content = """AAAA-BBBB-CCCC-DDDD
TEST-1234-5678-ABCD
INVALID-KEY
DEMO-0000-0000-0001
"""
    keys = license_service.parse_license_file(file_content)
    assert len(keys) == 3  # Only 3 valid keys
    assert "AAAA-BBBB-CCCC-DDDD" in keys
    assert "TEST-1234-5678-ABCD" in keys
    assert "DEMO-0000-0000-0001" in keys
    assert "INVALID-KEY" not in keys


def test_activate_license_success(api_client, db_session):
    """TC-LICENSE-04: Activate license (success path)"""
    # Create user
    user = create_user(db_session, "testuser", "testuser@example.com", password="secret123")
    
    # Create license
    license = models.License(license_key="TEST-1234-5678-ABCD", is_active=True)
    db_session.add(license)
    db_session.commit()
    
    # Login to get token
    token = login_user(db_session, "testuser", "secret123")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Activate license
    response = api_client.post(
        "/licenses/activate",
        json={"license_key": "TEST-1234-5678-ABCD"},
        headers=headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["license_key"] == "TEST-1234-5678-ABCD"
    assert "activated_at" in data
    
    # Verify license has been marked as used
    db_session.refresh(license)
    assert license.is_active == False
    
    # Verify user-license association has been created
    user_license = db_session.query(models.UserLicense).filter(
        models.UserLicense.user_id == user.id
    ).first()
    assert user_license is not None
    assert user_license.license_id == license.id


def test_activate_license_invalid_format(api_client, db_session):
    """TC-LICENSE-05: Activate license (invalid format)"""
    user = create_user(db_session, "testuser2", "testuser2@example.com", password="secret123")
    token = login_user(db_session, "testuser2", "secret123")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = api_client.post(
        "/licenses/activate",
        json={"license_key": "INVALID-FORMAT"},
        headers=headers
    )
    
    assert response.status_code == 400
    assert "Invalid license key format" in response.json()["detail"]


def test_activate_license_not_found(api_client, db_session):
    """TC-LICENSE-06: Activate license (license not found)"""
    user = create_user(db_session, "testuser3", "testuser3@example.com", password="secret123")
    token = login_user(db_session, "testuser3", "secret123")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = api_client.post(
        "/licenses/activate",
        json={"license_key": "NONE-0000-0000-0000"},
        headers=headers
    )
    
    assert response.status_code == 400
    assert "License key not found" in response.json()["detail"]


def test_activate_license_already_used(api_client, db_session):
    """TC-LICENSE-07: Activate license (license already used)"""
    user1 = create_user(db_session, "user1", "user1@example.com", password="secret123")
    user2 = create_user(db_session, "user2", "user2@example.com", password="secret123")
    
    # Create license and activate for user1
    license = models.License(license_key="USED-0000-0000-0001", is_active=True)
    db_session.add(license)
    db_session.commit()
    
    user_license = models.UserLicense(user_id=user1.id, license_id=license.id)
    license.is_active = False
    db_session.add(user_license)
    db_session.commit()
    
    # user2 tries to activate the same license
    token2 = login_user(db_session, "user2", "secret123")
    headers2 = {"Authorization": f"Bearer {token2}"}
    
    response = api_client.post(
        "/licenses/activate",
        json={"license_key": "USED-0000-0000-0001"},
        headers=headers2
    )
    
    assert response.status_code == 400
    assert "already been used" in response.json()["detail"]


def test_activate_license_user_already_has_license(api_client, db_session):
    """TC-LICENSE-08: Activate license (user already has license)"""
    user = create_user(db_session, "testuser4", "testuser4@example.com", password="secret123")
    
    # Create and activate first license
    license1 = models.License(license_key="FIRS-0000-0000-0001", is_active=True)
    db_session.add(license1)
    db_session.commit()
    
    user_license1 = models.UserLicense(user_id=user.id, license_id=license1.id)
    license1.is_active = False
    db_session.add(user_license1)
    db_session.commit()
    
    # Create second license
    license2 = models.License(license_key="SECO-0000-0000-0002", is_active=True)
    db_session.add(license2)
    db_session.commit()
    
    # Try to activate second license
    token = login_user(db_session, "testuser4", "secret123")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = api_client.post(
        "/licenses/activate",
        json={"license_key": "SECO-0000-0000-0002"},
        headers=headers
    )
    
    assert response.status_code == 400
    assert "already has an active license" in response.json()["detail"]


def test_get_license_status_with_license(api_client, db_session):
    """TC-LICENSE-09: Get license status (with license)"""
    user = create_user(db_session, "testuser5", "testuser5@example.com", password="secret123")
    
    license = models.License(license_key="STATUS-0000-0000-0001", is_active=True)
    db_session.add(license)
    db_session.commit()
    
    user_license = models.UserLicense(user_id=user.id, license_id=license.id)
    license.is_active = False
    db_session.add(user_license)
    db_session.commit()
    
    token = login_user(db_session, "testuser5", "secret123")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = api_client.get("/licenses/status", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["has_license"] == True
    assert data["license_key"] == "STATUS-0000-0000-0001"
    assert "activated_at" in data


def test_get_license_status_without_license(api_client, db_session):
    """TC-LICENSE-10: Get license status (without license)"""
    user = create_user(db_session, "testuser6", "testuser6@example.com", password="secret123")
    token = login_user(db_session, "testuser6", "secret123")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = api_client.get("/licenses/status", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["has_license"] == False
    assert data["license_key"] is None
    assert data["activated_at"] is None


def test_access_without_license(api_client, db_session):
    """TC-LICENSE-11: Access protected endpoint without license"""
    user = create_user(db_session, "testuser7", "testuser7@example.com", password="secret123")
    token = login_user(db_session, "testuser7", "secret123")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to access endpoint that requires license
    response = api_client.get("/projects", headers=headers)
    
    assert response.status_code == 403
    assert "Valid license required" in response.json()["detail"]


def test_access_with_license(api_client, db_session):
    """TC-LICENSE-12: Access protected endpoint with license"""
    user = create_user(db_session, "testuser8", "testuser8@example.com", password="secret123")
    
    # Create and activate license
    license = models.License(license_key="ACCESS-0000-0000-0001", is_active=True)
    db_session.add(license)
    db_session.commit()
    
    user_license = models.UserLicense(user_id=user.id, license_id=license.id)
    license.is_active = False
    db_session.add(user_license)
    db_session.commit()
    
    token = login_user(db_session, "testuser8", "secret123")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Access endpoint that requires license
    response = api_client.get("/projects", headers=headers)
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_upload_license_file(api_client, db_session):
    """TC-LICENSE-13: Upload license file"""
    user = create_user(db_session, "testuser9", "testuser9@example.com", password="secret123")
    
    # Create license
    license = models.License(license_key="FILE-0000-0000-0001", is_active=True)
    db_session.add(license)
    db_session.commit()
    
    token = login_user(db_session, "testuser9", "secret123")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create temporary file content
    file_content = "FILE-0000-0000-0001\nINVALID-KEY\nANOTHER-0000-0000-0002"
    
    # Simulate file upload
    response = api_client.post(
        "/licenses/upload",
        files={"file": ("license.txt", file_content, "text/plain")},
        headers=headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert len(data) == 1
    assert data[0]["license_key"] == "FILE-0000-0000-0001"
    
    # Verify license has been used
    db_session.refresh(license)
    assert license.is_active == False


def test_check_user_has_license(db_session):
    """TC-LICENSE-14: Check if user has license (service layer)"""
    user = create_user(db_session, "testuser10", "testuser10@example.com", password="secret123")
    
    # No license
    assert license_service.check_user_has_license(user) == False
    
    # Create and activate license
    license = models.License(license_key="CHECK-0000-0000-0001", is_active=True)
    db_session.add(license)
    db_session.commit()
    
    user_license = models.UserLicense(user_id=user.id, license_id=license.id)
    license.is_active = False
    db_session.add(user_license)
    db_session.commit()
    
    # Refresh user object to load relationships
    db_session.refresh(user)
    
    # Has license
    assert license_service.check_user_has_license(user) == True

