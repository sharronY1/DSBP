"""
Create admin user script
"""
import sys
from backend.database import SessionLocal
from backend.models import User
from backend.utils.auth import get_password_hash

def create_admin_user(email: str, username: str, password: str):
    """Create an admin user"""
    db = SessionLocal()
    try:
        # Check if admin already exists
        existing_user = db.query(User).filter(
            (User.email == email) | (User.username == username)
        ).first()
        
        if existing_user:
            print(f"User with email {email} or username {username} already exists!")
            return False
        
        # Create admin user
        admin_user = User(
            email=email,
            username=username,
            password_hash=get_password_hash(password),
            role=User.UserRole.ADMIN,
            license_type=User.LicenseType.PAID,  # Admin gets paid license
            is_active=True,
            is_email_verified=True,
        )
        
        db.add(admin_user)
        db.commit()
        print(f"Admin user created successfully!")
        print(f"Email: {email}")
        print(f"Username: {username}")
        return True
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python create_admin.py <email> <username> <password>")
        sys.exit(1)
    
    email = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    
    create_admin_user(email, username, password)

