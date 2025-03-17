from sqlmodel import create_engine, SQLModel, Session
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get the database URL from the environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Create the database engine
engine = create_engine(DATABASE_URL)

# Function to create database tables
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Function to get a database session
def get_session():
    with Session(engine) as session:
        yield session