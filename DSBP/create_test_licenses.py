"""Script for creating test licenses"""
from app.core.database import SessionLocal, engine
from app.models import Base, License
import app.models as models

# Create tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Create some test licenses
test_licenses = [
    "AAAA-BBBB-CCCC-DDDD",
    "TEST-1234-5678-ABCD",
    "DEMO-0000-0000-0001",
    "SAMPLE-0000-0000-0002",
    "VALID-0000-0000-0003",
]

for key in test_licenses:
    existing = db.query(License).filter(License.license_key == key).first()
    if not existing:
        license = License(license_key=key, is_active=True)
        db.add(license)
        print(f"Created license: {key}")
    else:
        print(f"License already exists: {key}")

db.commit()
db.close()
print("Licenses created successfully!")
print("\nYou can use any of these license keys to activate your account:")
for key in test_licenses:
    print(f"  - {key}")

