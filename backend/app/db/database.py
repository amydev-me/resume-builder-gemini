# backend/app/db/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite database URL
# The `///` after sqlite: means it's a relative path to the current working directory.
# We'll put it in the `data` directory.
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/sql_app.db"

# Create the SQLAlchemy engine
# connect_args={"check_same_thread": False} is needed for SQLite when using multiple threads,
# which FastAPI does. For other databases like PostgreSQL, you won't need this.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Each instance of SessionLocal class will be a database session.
# The class itself is not a SQLAlchemy Session.
# We'll use instances of SessionLocal in our code.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our database models.
Base = declarative_base()

# Dependency to get a database session for each request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()