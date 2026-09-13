from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Some hosts (Render, Heroku, etc.) hand out connection strings using the
# legacy "postgres://" scheme, which SQLAlchemy's psycopg2 dialect no
# longer accepts - normalize it to "postgresql://".
_database_url = settings.DATABASE_URL
if _database_url.startswith("postgres://"):
    _database_url = _database_url.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if _database_url.startswith("sqlite") else {}
engine = create_engine(_database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
