from sqlalchemy import create_engine

DATABASE_URL = "postgresql://habishek@localhost/login_app"

engine = create_engine(DATABASE_URL)
