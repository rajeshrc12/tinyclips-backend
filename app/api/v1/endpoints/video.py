from fastapi import APIRouter
from moviepy.editor import VideoClip, AudioFileClip
import os
from app.schemas.video import VideoRequest
from app.services.video import update_balance, update_video
from app.services.replicate import generate_audio
from app.services.assembly import transcribe_audio
from app.services.nebius import create_image_prompts, generate_image
from app.services.wasabi import upload_video
from app.utils.audio import get_audio_in_bytes
from app.utils.video import make_frame
from app.utils.subtitle import split_time_series, get_subtitle_with_image_index
from concurrent.futures import ThreadPoolExecutor
from app.config.settings import IMAGE_PRICE

import tempfile


router = APIRouter()


@router.get("/")
def hello():
    return {"message": "Unathorized user"}


@router.post("/")
def create(video_data: VideoRequest):
    prompt = video_data.prompt
    user_id = video_data.userId
    video_id = video_data.videoId
    image_style = video_data.imageStyle
    voice_speed = video_data.voiceSpeed
    voice_name = video_data.voiceName
    estimated_charges = video_data.estimatedCharges

    audio_link = generate_audio(
        prompt, voice_speed, voice_name)
    audio = get_audio_in_bytes(audio_link)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio_file:
        temp_audio_file.write(audio.getvalue())
        temp_audio_file_path = temp_audio_file.name
    subtitles, subtitles_segment = transcribe_audio(temp_audio_file_path)
    subtitles_time_series = split_time_series(subtitles_segment)
    subtitle_with_image_index = get_subtitle_with_image_index(
        subtitles_time_series)

    image_prompts = []
    with ThreadPoolExecutor() as executor:
        results = executor.map(
            lambda item: create_image_prompts(
                prompt, item["word"], len(item["series"]), image_style),
            subtitles_time_series
        )

    for res in results:
        image_prompts += res

    with ThreadPoolExecutor() as executor:
        background_images = list(executor.map(generate_image, image_prompts))

    audio_clip = AudioFileClip(temp_audio_file_path)

    video_clip = VideoClip(lambda t: make_frame(
        t, background_images, subtitles, subtitle_with_image_index), duration=audio_clip.duration)

    # 10% of audio duration, max 0.5s
    fade_duration = min(0.5, audio_clip.duration * 0.1)
    audio_clip = audio_clip.audio_fadeout(fade_duration)
    video_clip = video_clip.set_audio(audio_clip)
    video_link = upload_video(video_clip, video_id)
    audio_clip.close()
    os.remove(temp_audio_file_path)
    if video_link:
        update_video(video_id, len(background_images), audio_clip.duration)
        image_price = round(float(IMAGE_PRICE), 4)
        actual_charges = len(background_images) * image_price
        actual_charges = round(actual_charges, 4)
        final_charges = round(estimated_charges - actual_charges, 4)
        print(estimated_charges, actual_charges, final_charges)
        update_balance(user_id, final_charges)

    return video_link
