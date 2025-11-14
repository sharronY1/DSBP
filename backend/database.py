"""
DSBP Database Configuration
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import urlparse
import sys
import os
from backend.config import settings

# Set UTF-8 encoding for Windows to avoid psycopg2 encoding issues
if sys.platform == 'win32':
    # Set multiple environment variables to force UTF-8
    os.environ['PGCLIENTENCODING'] = 'UTF8'
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    # Try to set locale to UTF-8 if possible
    try:
        import locale
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'C.UTF-8')
        except:
            pass  # Keep default locale if UTF-8 not available

# Parse DATABASE_URL and create engine using connection parameters to avoid encoding issues
def create_db_engine():
    """Create database engine handling Windows encoding issues"""
    db_url = settings.DATABASE_URL
    
    try:
        # Parse the URL
        parsed = urlparse(db_url)
        
        if parsed.scheme in ('postgresql', 'postgres'):
            # Extract components - ensure they are proper Unicode strings
            username = str(parsed.username) if parsed.username else None
            password = str(parsed.password) if parsed.password else None
            hostname = str(parsed.hostname) if parsed.hostname else 'localhost'
            port = int(parsed.port) if parsed.port else 5432
            database = str(parsed.path.lstrip('/')) if parsed.path else 'postgres'
            
            # Create a custom connection creator that uses psycopg2.connect with parameters
            # This completely bypasses URL string parsing
            # Ensure all parameters are properly encoded as UTF-8 strings
            def connect():
                import psycopg2
                # Ensure all parameters are proper UTF-8 strings
                safe_host = str(hostname).encode('utf-8', errors='replace').decode('utf-8')
                safe_db = str(database).encode('utf-8', errors='replace').decode('utf-8')
                safe_user = str(username).encode('utf-8', errors='replace').decode('utf-8') if username else None
                safe_pass = str(password).encode('utf-8', errors='replace').decode('utf-8') if password else None
                
                # Use psycopg2.connect with explicit parameters
                # This should avoid DSN string parsing issues
                return psycopg2.connect(
                    host=safe_host,
                    port=port,
                    dbname=safe_db,
                    user=safe_user,
                    password=safe_pass,
                    client_encoding='UTF8'
                )
            
            # Use a simple URL and override the connect function
            # This avoids all URL parsing issues
            simple_url = f"postgresql+psycopg2://"
            
            return create_engine(
                simple_url,
                creator=connect,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
            )
    except Exception as e:
        # Fallback: try original URL
        print(f"Warning: Error creating engine with custom creator: {e}", file=sys.stderr)
        try:
            # Ensure URL is valid UTF-8
            if isinstance(db_url, bytes):
                db_url = db_url.decode('utf-8', errors='replace')
            
            return create_engine(
                db_url,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                connect_args={"client_encoding": "utf8"} if "postgresql" in db_url or "postgres" in db_url else {},
            )
        except Exception as final_error:
            print(f"Fatal error creating database engine: {final_error}", file=sys.stderr)
            raise

engine = create_db_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

