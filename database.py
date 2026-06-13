import os
from sqlalchemy import create_engine

# 1. Checks Railway's environment variable first. If it's not found, it falls back to your local setup.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://habishek@localhost/login_app")

# 2. Fixes an old SQLAlchemy bug where it doesn't recognize "postgres://" links from platforms like Railway
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
