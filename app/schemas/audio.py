from sqlmodel import SQLModel
# Audio Schema & Model
class AudioBase(SQLModel):
    video_id: int

class AudioCreate(AudioBase):
    pass

class AudioRead(AudioBase):
    id: int