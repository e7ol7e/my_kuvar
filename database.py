from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/todo_db"
)

engine = create_engine(DATABASE_URL, echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session