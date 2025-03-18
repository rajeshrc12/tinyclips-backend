from sqlmodel import Session, select
from app.models.video import Video
from app.schemas.video import VideoCreate, VideoUpdate

# Create Video
def create_video(session: Session, video_data: VideoCreate) -> Video:
    video = Video(**video_data.dict())
    session.add(video)
    session.commit()
    session.refresh(video)
    return video

# Get Video by ID
def get_video(session: Session, video_id: int) -> Video | None:
    return session.get(Video, video_id)

# Get All Videos
def get_all_videos(session: Session, skip: int = 0, limit: int = 10):
    statement = select(Video).offset(skip).limit(limit)
    return session.exec(statement).all()

# Update Video
def update_video(session: Session, video_id: int, video_data: VideoUpdate) -> Video | None:
    video = session.get(Video, video_id)
    if not video:
        return None
    video_data_dict = video_data.dict(exclude_unset=True)
    for key, value in video_data_dict.items():
        setattr(video, key, value)
    session.add(video)
    session.commit()
    session.refresh(video)
    return video

# Delete Video
def delete_video(session: Session, video_id: int) -> bool:
    video = session.get(Video, video_id)
    if not video:
        return False
    session.delete(video)
    session.commit()
    return True
