from fastapi import FastAPI
from app.database.connection import create_db_and_tables
from app.api.v1.endpoints.todo import router as todo_router
from app.api.v1.endpoints.video import router as video_router
from app.api.v1.endpoints.auth import router as auth_router

app = FastAPI()

app.include_router(todo_router, prefix="/api/v1/todo")
app.include_router(video_router, prefix="/api/v1/video")
app.include_router(auth_router, prefix="/api/v1/auth")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()