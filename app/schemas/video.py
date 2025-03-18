from sqlmodel import SQLModel
from typing import Optional
from app.models.video import VideoStatus  # Importing Enum from your model

# Base Schema (Shared attributes)
class VideoBase(SQLModel):
    user_id: int
    script: str
    image_style: str
    voice: str
    speed: float
    is_subtitle: bool
    subtitle_color: str
    subtitle_size: int

# Schema for creating a video
class VideoCreate(VideoBase):
    pass

# Schema for reading video data
class VideoRead(VideoBase):
    id: int
    status: VideoStatus

# Schema for updating a video
class VideoUpdate(SQLModel):
    script: Optional[str] = None
    image_style: Optional[str] = None
    voice: Optional[str] = None
    speed: Optional[float] = None
    is_subtitle: Optional[bool] = None
    subtitle_color: Optional[str] = None
    subtitle_size: Optional[int] = None
    status: Optional[VideoStatus] = None
