import boto3
import os
from app.config.settings import WASABI_ACCESS_KEY, WASABI_SECRET_KEY, WASABI_ENDPOINT, WASABI_BUCKET_NAME
import tempfile
from io import BytesIO

s3_client = boto3.client(
    "s3",
    aws_access_key_id=WASABI_ACCESS_KEY,
    aws_secret_access_key=WASABI_SECRET_KEY,
    endpoint_url=f"https://{WASABI_ENDPOINT}"
)


def upload_video(video, object_name):
    try:
        # Create a BytesIO buffer to store the video
        video_buffer = BytesIO()

        # Use a temporary file path to store the video data as an MP4 file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video_file:
            video_temp_path = temp_video_file.name  # Save the temporary file path

        # Write the video to the temporary file path with MP4 format (30 FPS)
        video.write_videofile(video_temp_path, codec='libx264',
                              audio_codec='aac', fps=24, threads=4, preset='ultrafast')

        # Open the temporary video file to load into a buffer
        with open(video_temp_path, 'rb') as video_file:
            video_buffer.write(video_file.read())

        # Seek to the beginning of the buffer after writing
        video_buffer.seek(0)

        # Upload the video to the Wasabi bucket
        s3_client.upload_fileobj(
            video_buffer, WASABI_BUCKET_NAME, f"video/{object_name}.mp4")
        print(
            f"Video successfully uploaded to Wasabi bucket: {WASABI_BUCKET_NAME}/video/{object_name}")

        os.remove(video_temp_path)
        return True

    except Exception as e:
        print(f"Error uploading file to Wasabi: {e}")
        return False
