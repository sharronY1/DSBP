"""License management service for validating and activating licenses."""

import re
import secrets
import string
from typing import Optional
from sqlalchemy.orm import Session

import app.models as models

# License key format: AAAA-BBBB-CCCC-DDDD (4 alphanumeric groups separated by -)
LICENSE_KEY_PATTERN = re.compile(r'^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$')

# Character set for generating license keys (uppercase letters and digits, excluding confusing characters)
LICENSE_CHARS = string.ascii_uppercase + string.digits
# Exclude confusing characters: 0, O, I, 1
LICENSE_CHARS = LICENSE_CHARS.replace('0', '').replace('O', '').replace('I', '').replace('1', '')


def generate_license_key() -> str:
    """Generate a random license key in format AAAA-BBBB-CCCC-DDDD"""
    # Use cryptographically secure random number generator
    segments = []
    for _ in range(4):
        segment = ''.join(secrets.choice(LICENSE_CHARS) for _ in range(4))
        segments.append(segment)
    return '-'.join(segments)


def validate_license_key_format(license_key: str) -> bool:
    """Validate if the license key format is correct"""
    return bool(LICENSE_KEY_PATTERN.match(license_key.upper().strip()))


def normalize_license_key(license_key: str) -> str:
    """Normalize license key (convert to uppercase, strip whitespace)"""
    return license_key.upper().strip()


def parse_license_file(file_content: str) -> list[str]:
    """Parse license keys from file content (one key per line)"""
    keys = []
    for line in file_content.strip().split('\n'):
        key = line.strip()
        if key and validate_license_key_format(key):
            keys.append(normalize_license_key(key))
    return keys


def check_user_has_license(user: models.User) -> bool:
    """Check if user has an activated license"""
    return user.license is not None


def activate_license_for_user(user_id: int, license_key: str, db: Session) -> models.UserLicense:
    """Activate a license for a user"""
    normalized_key = normalize_license_key(license_key)
    
    # Validate format
    if not validate_license_key_format(normalized_key):
        raise ValueError("Invalid license key format. Expected: AAAA-BBBB-CCCC-DDDD")
    
    # Find license
    license = db.query(models.License).filter(
        models.License.license_key == normalized_key
    ).first()
    
    if not license:
        raise ValueError("License key not found")
    
    if not license.is_active:
        raise ValueError("License key has already been used")
    
    # Check if user already has a license
    existing = db.query(models.UserLicense).filter(
        models.UserLicense.user_id == user_id
    ).first()
    
    if existing:
        raise ValueError("User already has an active license")
    
    # Create user-license association
    user_license = models.UserLicense(
        user_id=user_id,
        license_id=license.id
    )
    
    # Mark license as used
    license.is_active = False
    
    db.add(user_license)
    db.commit()
    db.refresh(user_license)
    
    return user_license
