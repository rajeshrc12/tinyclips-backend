from sqlmodel import SQLModel, Field
from typing import Optional

class Audio(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    video_id: int = Field(foreign_key="video.id")
