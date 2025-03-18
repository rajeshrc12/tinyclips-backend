from sqlmodel import SQLModel, Field
from typing import Optional
from enum import Enum

class VideoStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class Video(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    script: str
    image_style: str
    voice: str
    speed: float 
    is_subtitle: bool
    subtitle_color: str
    subtitle_size: int
    status: VideoStatus = Field(default=VideoStatus.PENDING)
