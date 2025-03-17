from fastapi import FastAPI
from app.database.connection import create_db_and_tables
from app.api.v1.endpoints.todo import router as todo_router

app = FastAPI()

app.include_router(todo_router, prefix="/api/v1")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()