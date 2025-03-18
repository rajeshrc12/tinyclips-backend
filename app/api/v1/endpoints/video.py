from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from moviepy.editor import VideoClip,AudioFileClip
import os
from app.schemas.video import VideoCreate, VideoRead, VideoUpdate
from app.services.video import (
    create_video,
    get_video,
    get_all_videos,
    update_video,
    delete_video,
)
from app.database.connection import get_session  # Correct import
from app.services.replicate import generate_audio,generate_image
from app.services.wasabi import upload_audio,upload_subtitle,upload_video
from app.services.whisper import transcribe_audio
from app.utils.subtitle import split_time_series,get_subtitle_with_image_index
from app.utils.audio import get_audio_in_bytes
from app.utils.image import create_new_image_prompt,make_frame
from app.services.gemini import create_image_prompts
import tempfile


router = APIRouter()

# Create Video
@router.post("/", response_model=VideoRead)
def create(video_data: VideoCreate, session: Session = Depends(get_session)):
    video = create_video(session, video_data)
    video_id = video.id 
    image_style = ""
    audio_link = generate_audio(video_data.script,video_data.speed,video_data.voice)
    audio = get_audio_in_bytes(audio_link)
    # upload_audio(audio_link,video_id)
    subtitles, subtitles_segment = transcribe_audio(audio)
    # upload_subtitle(subtitles, subtitles_segment,video_id)
    subtitles_time_series = split_time_series(subtitles_segment)
    subtitle_with_image_index = get_subtitle_with_image_index(subtitles_time_series)
    image_prompts=[]
    for item in subtitles_time_series:
        image_prompts+= create_image_prompts(item["word"],len(item["series"]))

    images = []
    for index, prompt in enumerate(image_prompts):
        new_prompt = create_new_image_prompt(prompt,image_style)
        images.append(generate_image(new_prompt,index,len(image_prompts)))

    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio_file:
        temp_audio_file.write(audio.getvalue())  # Write the content of BytesIO to the file
        temp_audio_file_path = temp_audio_file.name  # Get the path to the temporary file

    audio_clip = AudioFileClip(temp_audio_file_path)
    print(subtitle_with_image_index)
    video_clip = VideoClip(lambda t: make_frame(t, images,subtitles,subtitle_with_image_index), duration=audio_clip.duration)

    video_clip = video_clip.set_audio(audio_clip)
    upload_video(video_clip,video_id)

    audio_clip.close()
    os.remove(temp_audio_file_path)
    return video

# Get Video by ID
@router.get("/{video_id}", response_model=VideoRead)
def read(video_id: int, session: Session = Depends(get_session)):
    video = get_video(session, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video

# Get All Videos
@router.get("/", response_model=list[VideoRead])
def read_all(skip: int = 0, limit: int = 10, session: Session = Depends(get_session)):
    return get_all_videos(session, skip, limit)

# Update Video
@router.put("/{video_id}", response_model=VideoRead)
def update(video_id: int, video_data: VideoUpdate, session: Session = Depends(get_session)):
    updated_video = update_video(session, video_id, video_data)
    if not updated_video:
        raise HTTPException(status_code=404, detail="Video not found")
    return updated_video

# Delete Video
@router.delete("/{video_id}", status_code=204)
def delete(video_id: int, session: Session = Depends(get_session)):
    if not delete_video(session, video_id):
        raise HTTPException(status_code=404, detail="Video not found")
