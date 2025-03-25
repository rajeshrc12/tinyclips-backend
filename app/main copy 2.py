
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi import FastAPI
import os
from dotenv import load_dotenv
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip, VideoClip
import numpy as np
import requests
import tempfile
import boto3
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import List
import json
import replicate
import google.generativeai as genai
import assemblyai as aai
from openai import OpenAI
import psycopg

FONT_PATH = Path(__file__).parent / "eng.ttf"

app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now; restrict as needed
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)


# Load environment variables from .env file
load_dotenv()

WASABI_ACCESS_KEY = os.getenv("WASABI_ACCESS_KEY")
WASABI_SECRET_KEY = os.getenv("WASABI_SECRET_KEY")
WASABI_ENDPOINT = os.getenv("WASABI_ENDPOINT")
WASABI_BUCKET_NAME = os.getenv("WASABI_BUCKET_NAME")
FIREWORK_API_KEY = os.getenv("FIREWORK_API_KEY")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
GEMINI_API_TOKEN = os.getenv("GEMINI_API_TOKEN")
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")


aai.settings.api_key = ASSEMBLYAI_API_KEY

s3_client = boto3.client(
    "s3",
    aws_access_key_id=WASABI_ACCESS_KEY,
    aws_secret_access_key=WASABI_SECRET_KEY,
    endpoint_url=f"https://{WASABI_ENDPOINT}"
)

genai.configure(api_key=GEMINI_API_TOKEN)
gemini_model = genai.GenerativeModel("gemini-2.0-flash-lite")

client = OpenAI(
    base_url="https://api.studio.nebius.com/v1/",
    api_key=NEBIUS_API_KEY
)


# def create_image_prompts(script, image_prompts_count):
#     print("Generating prompts from script...", script)
#     script_template = f"""
# You are an expert portrait image prompt generator.
# Read the script thoroughly to understand its overall context and theme.
# Generate a detailed portrait image prompt that visually represents the content, emotion, facial expressions and atmosphere for a compelling portrait representation.
# Ensure that each prompt maintains relevance and aligns with the sequence of the script to preserve its flow.
# If the script references a product, service, or advertisement, create a relevant object in the scene with appropriate text, symbols ensuring it blends naturally with the surroundings.
# The total number of prompts should be equal to {image_prompts_count} and ensure the entire script is represented.

# Return the output as an array of prompts in the following format:
# [
# "First prompt description",
# "Second prompt description",
# ...
# "Last prompt description"
# ]
# Ensure there are no extra keys, indices, or labels — only the prompts enclosed in double quotes within the array.
# Script : "{script}"
#     """
#     try:
#         # Generate the response from the model
#         response = gemini_model.generate_content(script_template).text
#         # Remove the surrounding brackets and parse the list
#         start = response.find('[')
#         end = response.rfind(']') + 1

#         print("All prompts generated !!!")

#         # Extract the string between the brackets and strip any leading or trailing whitespace
#         image_prompts = json.loads(response[start:end].strip())

#         return image_prompts
#     except Exception as e:
#         print(str(e))
#         return []

def create_image_prompts(main_script, sub_script):
    print("Generating prompts from script...", sub_script)
    script_template = f"""
Read and thoroughly understand the following Main Script to grasp its full context:
Main Script:
"{main_script}"

Now, analyze the Sub-Script, which is a part of the Main Script. Your task is to generate only one single highly relevant and visually compelling portrait image prompt that aligns with both the Sub-Script and the broader context of the Main Script.
Accurately depict the scene, emotions, facial expressions, and overall atmosphere.
Ensure the visual elements reinforce the essence and tone of the Sub-script.
If the Sub-Script references a product, service, or advertisement, incorporate it naturally within the scene. Use appropriate text, symbols, or objects to blend seamlessly into the environment.

Sub-Script:
"{sub_script}"

In response ensure there are no extra keys, indices, or labels — only the prompt enclosed in double quotes.
    """
    try:
        # Generate the response from the model
        response = gemini_model.generate_content(script_template).text
        print("start", "\n", sub_script, "\n", response, "end", "\n")
        return response
    except Exception as e:
        print(str(e))
        return False


def fetch_image(url):
    response = requests.get(url)
    image = Image.open(BytesIO(response.content)).convert("RGB")
    return np.array(image)


def fetch_audio(url):
    response = requests.get(url)
    return response.content


def generate_audio(script, speed=0.9, voice="am_adam"):
    print("Generating speech...")
    output = replicate.run(
        "jaaari/kokoro-82m:f559560eb822dc509045f3921a1921234918b91739db4bf3daab2169b71c7a13",
        input={
            "text": script,
            "speed": speed,
            "voice": voice
        }
    )
    # output = "https://replicate.delivery/czjl/ZpQ6y6VCoBZcDxuWJbp9rwXgTbUhgVUzwRn2iDiTXSxpZhCF/output.wav"
    if output:
        print("Generating speech completed!!!")
        return output
    else:
        print("Failed to create the audio file.")
        return False


def create_text_clip(text, duration):
    img = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, 70)
    text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:]
    draw.text(((1920 - text_width) / 2, (1080 - text_height) / 2), text,
              fill="white", font=font, stroke_width=5, stroke_fill="black")
    return ImageClip(np.array(img)).set_duration(duration)


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

        # Create a boto3 client to interact with Wasabi (using AWS S3 SDK)
        s3_client = boto3.client(
            's3',
            endpoint_url='https://'+WASABI_ENDPOINT,
            aws_access_key_id=WASABI_ACCESS_KEY,
            aws_secret_access_key=WASABI_SECRET_KEY
        )

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


def create_new_image_prompt(prompt, image_style):
    new_prompt = prompt
    if image_style:
        new_prompt = f"Create {image_style} style image of " + prompt
    print(new_prompt)
    return new_prompt


def get_prompt_by_time(result, time):
    for i, entry in enumerate(result):
        if entry['start'] <= time <= entry['end']:
            return i
    return len(result)-1


def make_frame(t, image_objects, subtitles, subtitles_segment):
    image_index = get_prompt_by_time(subtitles_segment, t)
    base_image = image_objects[image_index].copy()
    draw = ImageDraw.Draw(base_image)

    current_word = next(
        (subtitle['word'] for subtitle in subtitles if subtitle['start'] <= t <= subtitle['end']), "")

    font = ImageFont.truetype("eng.ttf", 70)
    text_width, text_height = draw.textbbox(
        (0, 0), current_word, font=font)[2:]
    text_x = (base_image.width - text_width) // 2
    text_y = (base_image.height - text_height) // 2

    draw.text((text_x, text_y), current_word, font=font,
              fill="white", stroke_width=5, stroke_fill="black")
    return np.array(base_image)


def get_audio_in_bytes(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Ensure the request was successful
        audio = BytesIO(response.content)
        return audio
    except Exception as e:
        print(f"Error fetching file from URL: {e}")
        return False


def transcribe_audio(audio):

    transcriber = aai.Transcriber()

    config = aai.TranscriptionConfig(
        speaker_labels=True, punctuate=True, format_text=True)

    transcript = transcriber.transcribe(audio, config)

    if transcript.status == aai.TranscriptStatus.error:
        print(f"Transcription failed: {transcript.error}")
        exit(1)

    subtitles_sentence = []
    for sentence in transcript.get_sentences():
        sentence_data = {
            "start": round(sentence.start / 1000, 2),  # Convert ms to sec
            "end": round(sentence.end / 1000, 2),
            "word": sentence.text
        }
        subtitles_sentence.append(sentence_data)

    output = []
    word = ""
    start = 0.0

    for i in range(len(subtitles_sentence)):
        if i + 1 == len(subtitles_sentence):
            output.append(
                {"start": start, "end": subtitles_sentence[i]["end"], "word": word + subtitles_sentence[i]["word"]})
            break

        if subtitles_sentence[i]["end"] == subtitles_sentence[i + 1]["start"]:
            word += subtitles_sentence[i]["word"] + " "
        else:
            output.append(
                {"start": start, "end": subtitles_sentence[i + 1]["start"], "word": word + subtitles_sentence[i]["word"]})
            word = ""
            start = subtitles_sentence[i + 1]["start"]

    subtitles_word = []
    for word in transcript.words:
        word_data = {
            "start": round(word.start / 1000, 2),
            "end": round(word.end / 1000, 2),
            "word": word.text
        }
        subtitles_word.append(word_data)

    return subtitles_word, output


def split_time_series(input_list, interval_length=2.0):
    """Process the input list and generate the desired output in one function."""
    output = []
    for interval in input_list:
        start = interval['start']
        end = interval['end']
        series = []
        current_start = start
        while current_start < end:
            current_end = min(current_start + interval_length, end)
            # If the remaining duration is less than the interval length, merge it with the previous interval
            if series and (current_end - current_start) < interval_length:
                # Merge with the previous interval
                series[-1]['end'] = current_end
            else:
                series.append({'start': current_start, 'end': current_end})
            current_start = current_end
        output.append({
            'start': start,
            'end': end,
            'series': series,
            'word': interval['word']
        })
    return output


def get_subtitle_with_image_index(data):
    count = 0
    subtitle_with_image_index = []
    for item in data:
        item["index"] = []
        for i, series in enumerate(item["series"]):
            series["index"] = count
            subtitle_with_image_index.append(series.copy())
            item["index"].append(count)
            count += 1
    return subtitle_with_image_index


# def generate_image(prompt, index=0, count=0):
#     if count:
#         print(f"->processing {index+1} image of {count}...")
#     output = replicate.run(
#         "black-forest-labs/flux-schnell",
#         input={
#             "prompt": prompt,
#             "go_fast": True,
#             "megapixels": "1",
#             "num_outputs": 1,
#             "aspect_ratio": "9:16",
#             "output_format": "png",
#             "output_quality": 80,
#             "num_inference_steps": 4
#         }
#     )
#     print(output)
#     if isinstance(output, list) and output:
#         file_output = output[0]  # Get the first FileOutput object

#         if isinstance(file_output, replicate.helpers.FileOutput):
#             # Read file content into memory
#             image_data = file_output.read()
#             # Convert to Pillow Image object
#             image = Image.open(BytesIO(image_data))
#             if count:
#                 print(f"->completed !!!")
#             return image
#         else:
#             print("Unexpected output format.")
#             return None
#     else:
#         print("Invalid response from Replicate API.")
#         return None

def generate_image(prompt, index=0, count=0):
    if count:
        print(f"->processing {index+1} image of {count}...")
        response = client.images.generate(
            model="black-forest-labs/flux-schnell",
            response_format="url",
            extra_body={
                "response_extension": "png",
                "width": 576,
                "height": 1024,
                "num_inference_steps": 4,
                "negative_prompt": "Distorted body, extra limbs, missing fingers, deformed face, unnatural proportions, incorrect spelling, gibberish text, extra eyes, extra fingers",
                "seed": -1
            },
            prompt=prompt
        )
        # Ensure response is parsed as JSON
        # Convert JSON string to dictionary
        data = json.loads(response.to_json())

        # Extract the image URL
        url = data["data"][0]["url"]
        print("Generated Image URL:", url)

        # Fetch and open the image
        response = requests.get(url)
        response.raise_for_status()  # Ensure we got a valid response

        # Convert to Pillow Image object
        image = Image.open(BytesIO(response.content))
        target_height = 1920
        aspect_ratio = image.width / image.height
        new_width = int(target_height * aspect_ratio)

        # Resize while keeping aspect ratio
        resized_image = image.resize((new_width, target_height), Image.LANCZOS)

        # Step 2: Center crop to 1080px width
        target_width = 1080
        left = (new_width - target_width) // 2
        right = left + target_width

        cropped_image = resized_image.crop((left, 0, right, target_height))
        print(f"completed!!!")
        return cropped_image


def update_image_count(video_id: str, new_count: int):
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # Use double quotes around "imageCount" to preserve case sensitivity
                query = 'UPDATE "Video" SET "imageCount" = %s WHERE id = %s'
                cur.execute(query, (new_count, video_id))
                conn.commit()
                print(
                    f"Updated video {video_id} with imageCount = {new_count}")

    except Exception as e:
        print("Error updating imageCount:", e)


def update_balance(user_id: str, charges: float):
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                query = 'UPDATE "User" SET balance = balance - %s WHERE id = %s RETURNING balance'
                cur.execute(query, (charges, user_id))
                updated_balance = cur.fetchone()

                if updated_balance is None:
                    print(f"User {user_id} not found.")
                    return None

                conn.commit()
                print(
                    f"Deducted {charges} from user {user_id}. New balance: {updated_balance[0]}")
                return updated_balance[0]
    except Exception as e:
        print(f"Error updating balance for user {user_id}: {e}")
        return None


class VideoRequest(BaseModel):
    userId: str
    videoId: str
    prompt: str
    imageStyle: str
    voiceName: str
    voiceSpeed: float


@app.get("/")
def get_message():
    {"message": "hello from Google cloud"}


@app.post("/")
def process_video(metadata: VideoRequest):
    # print(metadata.prompt)
    user_id = metadata.userId
    video_id = metadata.videoId
    image_style = metadata.imageStyle
    audio_link = generate_audio(
        metadata.prompt, metadata.voiceSpeed, metadata.voiceName)
    audio = get_audio_in_bytes(audio_link)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio_file:
        temp_audio_file.write(audio.getvalue())
        temp_audio_file_path = temp_audio_file.name
    subtitles, subtitles_segment = transcribe_audio(temp_audio_file_path)
    # subtitles_time_series = split_time_series(subtitles_segment)
    # subtitle_with_image_index = get_subtitle_with_image_index(
    #     subtitles_time_series)

    image_prompts = []
    with ThreadPoolExecutor() as executor:
        image_prompts = list(executor.map(lambda item: create_image_prompts(
            metadata.prompt, item["word"]), subtitles_segment))

    images = []
    # Parallel Image Generation using ThreadPoolExecutor
    with ThreadPoolExecutor() as executor:
        images = list(executor.map(
            lambda args: generate_image(*args),
            [(create_new_image_prompt(prompt, image_style), idx, len(image_prompts))
             for idx, prompt in enumerate(image_prompts)]
        ))

    audio_clip = AudioFileClip(temp_audio_file_path)
    video_clip = VideoClip(lambda t: make_frame(
        t, images, subtitles, subtitles_segment), duration=audio_clip.duration)

    video_clip = video_clip.set_audio(audio_clip)
    video_link = upload_video(video_clip, video_id)
    audio_clip.close()
    os.remove(temp_audio_file_path)
    if video_link:
        update_image_count(video_id, len(images))
        update_balance(user_id, len(images)*0.0013)
    # return video
    return {"url": ""}
