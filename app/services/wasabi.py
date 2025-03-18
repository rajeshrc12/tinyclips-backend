import boto3
import json
from botocore.exceptions import BotoCoreError, ClientError, EndpointConnectionError
from app.config.settings import WASABI_ACCESS_KEY, WASABI_SECRET_KEY, WASABI_ENDPOINT, WASABI_BUCKET_NAME
import tempfile
from io import BytesIO

s3_client = boto3.client(
    "s3",
    aws_access_key_id=WASABI_ACCESS_KEY,
    aws_secret_access_key=WASABI_SECRET_KEY,
    endpoint_url=f"https://{WASABI_ENDPOINT}"
)

async def upload_audio(audio, object_name):
    try:
        s3_client.upload_fileobj(audio, WASABI_BUCKET_NAME, f"audio/{object_name}.wav")
        return True
    except (BotoCoreError, ClientError, EndpointConnectionError) as e:
        print(f"Error uploading file to Wasabi: {e}")
        return False
    
async def upload_subtitle(subtitles, subtitles_segment,object_name):
    try:
        data={
            "word":subtitles,
            "segment":subtitles_segment
        }
        s3_client.put_object(
            Bucket=WASABI_BUCKET_NAME,
            Key=object_name,
            Body=json.dumps(data, indent=4),  # Convert JSON data to string
            ContentType='application/json'
        )
        return True
    except (BotoCoreError, ClientError, EndpointConnectionError) as e:
        print(f"Error uploading file to Wasabi: {e}")
        return False

def upload_video(video,object_name):
    try:
        # Create a BytesIO buffer to store the video
        video_buffer = BytesIO()
        
        # Use a temporary file path to store the video data as an MP4 file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video_file:
            video_temp_path = temp_video_file.name  # Save the temporary file path

        # Write the video to the temporary file path with MP4 format (30 FPS)
        video.write_videofile(video_temp_path, codec='libx264', audio_codec='aac', fps=30)

        # Open the temporary video file to load into a buffer
        with open(video_temp_path, 'rb') as video_file:
            video_buffer.write(video_file.read())
        
        # Seek to the beginning of the buffer after writing
        video_buffer.seek(0)

        # Create a boto3 client to interact with Wasabi (using AWS S3 SDK)
        s3_client = boto3.client(
            's3',
            endpoint_url='https://'+WASABI_ENDPOINT,
            aws_access_key_id=WASABI_ACCESS_KEY,
            aws_secret_access_key=WASABI_SECRET_KEY
        )

        # Upload the video to the Wasabi bucket
        s3_client.upload_fileobj(video_buffer, WASABI_BUCKET_NAME, f"video/{object_name}.mp4")
        print(f"Video successfully uploaded to Wasabi bucket: {WASABI_BUCKET_NAME}/video/{object_name}")
        
    except (BotoCoreError, ClientError, EndpointConnectionError) as e:
        print(f"Error uploading file to Wasabi: {e}")
        return False


