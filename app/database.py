import os
from dotenv import load_dotenv
from sqlmodel import create_engine, Session, SQLModel, text
from typing import Annotated
from fastapi import Depends

load_dotenv()
mysql_user = os.getenv("DATABASE_USER")
mysql_password = os.getenv("DATABASE_PASSWORD")
mysql_host = os.getenv("DATABASE_HOST")
mysql_port = os.getenv("DATABASE_PORT")
mysql_database_name = os.getenv("DATABASE_NAME")
mysql_url = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database_name}"

engine_db = create_engine(mysql_url , echo=True, pool_pre_ping=True, pool_recycle=3600)

def get_session():
    with Session(engine_db) as session:
        yield session



def test_database_connection():
    try:
        with Session(engine_db) as session:
            session.exec(text("SELECT 1"))
        print("Database connection successful!")
    except Exception as e:
        print(f"Database connection failed: {e}")


SessionDB1 = Annotated[Session, Depends(get_session)]
