from fastapi import FastAPI
from app.api.v1.endpoints.video import router as video_router

app = FastAPI()

app.include_router(video_router, prefix="/api/v1/video")
