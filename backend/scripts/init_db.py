"""
Database initialization script.
Run this to create all tables.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.base import engine, Base
# Import ALL models so they're registered with Base
from app.db.models.tenant import Tenant
from app.db.models.user import User
from app.db.models.document import Document
from app.db.models.chunk import Chunk
from app.db.models.chat_log import ChatLog
from app.db.models.feedback import Feedback

def init_db():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully!")
    
    # List created tables
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("\nTables in database:")
    for table in tables:
        print(f"  - {table}")

if __name__ == "__main__":
    init_db()