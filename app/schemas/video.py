from pydantic import BaseModel


class VideoRequest(BaseModel):
    userId: str
    videoId: str
    prompt: str
    imageStyle: str
    voiceName: str
    voiceSpeed: float
    estimatedCharges: float
