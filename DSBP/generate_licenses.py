"""Script to automatically generate license keys"""
import sys
from pathlib import Path

# Add project root directory to path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import SessionLocal, engine
from app.models import Base, License
from app.services.license import generate_license_key

# Create tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

def create_licenses(count: int = 5):
    """Generate specified number of license keys and save to database"""
    print(f"Generating {count} license keys...")
    print("-" * 50)
    
    created_keys = []
    for i in range(count):
        # Generate unique license key
        max_attempts = 100
        for attempt in range(max_attempts):
            key = generate_license_key()
            # Check if already exists
            existing = db.query(License).filter(License.license_key == key).first()
            if not existing:
                break
        else:
            print(f"Warning: Could not generate unique key after {max_attempts} attempts")
            continue
        
        # Create license record
        license = License(license_key=key, is_active=True)
        db.add(license)
        created_keys.append(key)
        print(f"{i+1}. {key}")
    
    db.commit()
    print("-" * 50)
    print(f"Successfully created {len(created_keys)} license keys!")
    print("\nGenerated license keys:")
    for key in created_keys:
        print(f"  - {key}")
    
    db.close()
    return created_keys

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate license keys")
    parser.add_argument(
        "-n", "--count",
        type=int,
        default=5,
        help="Number of license keys to generate (default: 5)"
    )
    
    args = parser.parse_args()
    create_licenses(args.count)

