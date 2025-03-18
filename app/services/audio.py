from app.models.audio import Audio
from app.schemas.audio import AudioCreate
from sqlmodel import Session

def create_audio(session: Session,audio: AudioCreate) -> Audio:
    db_audio = Audio(**audio.dict())
    session.add(db_audio)
    session.commit()
    session.refresh(db_audio)
    return db_audio.id

def delete_audio(session: Session,audio_id: int) -> bool:
    db_audio = session.get(Audio, audio_id)
    if not db_audio:
        return False
    session.delete(db_audio)
    session.commit()
    return True