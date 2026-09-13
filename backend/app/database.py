import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:securepassword@db:5432/fastapi_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency injection for API route endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
