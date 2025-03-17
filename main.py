#test
from pydantic import BaseModel
from fastapi import FastAPI
import os
import google.generativeai as genai
from dotenv import load_dotenv
import json
from pydub import AudioSegment
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, VideoClip
import numpy as np
import time
import whisper
import replicate
import requests
import random

app = FastAPI()

# Load environment variables from .env file
load_dotenv()

# GEMINI Config
GEMINI_API_TOKEN = os.getenv("GEMINI_API_KEY")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
genai.configure(api_key=GEMINI_API_TOKEN)
gemini_model = genai.GenerativeModel("gemini-2.0-flash")


def script_to_array_of_image_prompt(script,image_prompts_count):
    print("Generating prompts from script...",script)
    script_template = f"""
You are an expert portrait image prompt generator.
Read the script thoroughly to understand its overall context and theme.
Generate a detailed portrait image prompt that visually represents the content, emotion, facial expressions and atmosphere for a compelling portrait representation.
Ensure that each prompt maintains relevance and aligns with the sequence of the script to preserve its flow.
If the script references a product, service, or advertisement, create a relevant object in the scene with appropriate text, symbols ensuring it blends naturally with the surroundings.
The total number of prompts should be equal to {image_prompts_count} and ensure the entire script is represented.

Return the output as an array of prompts in the following format:
[
"First prompt description",
"Second prompt description",
...
"Last prompt description"
]
Ensure there are no extra keys, indices, or labels — only the prompts enclosed in double quotes within the array.
Script : "{script}"
    """
    try:
        # Generate the response from the model
        response = gemini_model.generate_content(script_template).text
        # Remove the surrounding brackets and parse the list
        start = response.find('[')
        end = response.rfind(']') + 1

        print("All prompts generated !!!")

        # Extract the string between the brackets and strip any leading or trailing whitespace
        image_prompts = json.loads(response[start:end].strip())

        return image_prompts
    except Exception as e:
        print(str(e))
        return []

def format_script(script):
    print("Formatting script...")
    script_template = f"""
    Analyze the given script and add commas and full stops in appropriate places to improve readability and meaning. Do not add, remove, or modify any words. Return only the formatted script without additional text or explanations.
    Script : "{script}"
    """

    # Generate the response from the model
    response = gemini_model.generate_content(script_template).text
    print(response)
    print("Formatting completed!!!")

    return response

def script_to_speech_using_replicate(script, audio_path, speed=0.9, voice="am_adam"):
    print("Generating speech...")
    output = replicate.run(
        "jaaari/kokoro-82m:f559560eb822dc509045f3921a1921234918b91739db4bf3daab2169b71c7a13",
        input={
            "text": script,
            "speed": speed,
            "voice": voice
        }
    )
    response = requests.get(output)
    if response.status_code == 200:
        wav_filename = "temp_audio.wav"

        # Save the WAV file locally
        with open(wav_filename, "wb") as file:
            file.write(response.content)

        # Convert WAV to MP3
        audio = AudioSegment.from_file(wav_filename, format="wav")
        audio.export(audio_path, format="mp3")
        duration_seconds = len(audio) / 1000
        print("Generating speech completed!!!")
        return duration_seconds
    else:
        print("Failed to download the audio file.")
        return 0

def generate_image_using_replicate(prompt):
    output = replicate.run(
        "black-forest-labs/flux-schnell",
        input={
            "prompt": prompt,
            "go_fast": True,
            "megapixels": "1",
            "num_outputs": 1,
            "aspect_ratio": "9:16",
            "output_format": "png",
            "output_quality": 80,
            "num_inference_steps": 4
        }
    )
    print(output)
    if isinstance(output, list) and output:
        file_output = output[0]  # Get the first FileOutput object

        if isinstance(file_output, replicate.helpers.FileOutput):
            # Read file content into memory
            image_data = file_output.read()
            # Convert to Pillow Image object
            image = Image.open(BytesIO(image_data))
            return image
        else:
            print("Unexpected output format.")
            return None
    else:
        print("Invalid response from Replicate API.")
        return None


def prompts_to_images(image_prompts, image_style=""):
    print("Generating images from prompts...")
    # image_prompts_count = len(image_prompts)
    # image_prompts = [image_prompts[0]]
    images = []
    for index, prompt in enumerate(image_prompts):
        print(f"->processing {index+1} image of {len(image_prompts)}...")
        new_prompt = prompt
        if image_style:
            new_prompt = f"Create {image_style} style image of " + prompt
        print(new_prompt)
        images.append(generate_image_using_replicate(
            new_prompt))
        print(f"->completed !!!")

    print(f"All images generated !!!")

    # return [images[0]] * image_prompts_count
    return images


def generate_subtitles_from_audio(audio_path):
    """
    Generate word-level subtitles from an audio file using Whisper.
    :param audio_path: Path to the audio file.
    :param output_subtitle_path: Path to save the subtitle file (e.g., .vtt or .srt).
    """
    # Load the Whisper model
    model = whisper.load_model("base")

    # Transcribe the audio file with word-level timestamps
    result_word = model.transcribe(audio_path, word_timestamps=True, fp16=False)
    result_segment = model.transcribe(audio_path, word_timestamps=False, fp16=False)
    # Extract words and their timestamps
    subtitles = []
    subtitles_segment = []
    for segment in result_word['segments']:
        for word_data in segment['words']:
            word = word_data['word']
            start = word_data['start']
            end = word_data['end']
            subtitles.append({"word": word, "start": start, "end": end})

    for segment in result_segment['segments']:
        word = segment['text']
        start = segment['start']
        end = segment['end']
        subtitles_segment.append({"word": word, "start": start, "end": end})

    return subtitles,subtitles_segment


# Function to generate frames
def make_frame(t,image_objects,subtitles,subtitle_with_image_index):
    image_index = get_prompt_by_time(subtitle_with_image_index,t)
    base_image = image_objects[image_index].copy()
    draw = ImageDraw.Draw(base_image)

    current_word = next((subtitle['word'] for subtitle in subtitles if subtitle['start'] <= t < subtitle['end']), "")

    font = ImageFont.truetype("default.ttf", 70)
    text_width, text_height = draw.textbbox((0, 0), current_word, font=font)[2:]
    text_x = (base_image.width - text_width) // 2
    text_y = (base_image.height - text_height) // 2

    draw.text((text_x, text_y), current_word, font=font, fill="white",stroke_width=5, stroke_fill="black")
    return np.array(base_image)

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
                series[-1]['end'] = current_end  # Merge with the previous interval
            else:
                series.append({'start': current_start, 'end': current_end})
            current_start = current_end
        output.append({
            'start': start,
            'end': end,
            'series': series,
            'word' : interval['word']
        })
    return output

def get_prompt_by_time(result, time):
    for entry in result:
        if entry['start'] <= time < entry['end']:
            return entry['index']
    return len(result)-1

def get_subtitle_with_image_index(data):
    count = 0
    subtitle_with_image_index=[]
    image_prompts=[]
    for item in data:
        item["index"] = []
        response = script_to_array_of_image_prompt(item["word"],len(item["series"]))
        image_prompts += response 
        for i,series in enumerate(item["series"]):
            series["index"]=count
            subtitle_with_image_index.append(series.copy())
            item["index"].append(count)
            count+=1
    return subtitle_with_image_index,image_prompts

def generate_random_color_images(num_images):
    images = []
    for _ in range(num_images):
        image = Image.new('RGB', (1080, 1920), (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255)
        ))
        images.append(image)
    return images

class VideoRequest(BaseModel):
    script: str

@app.post("/")
def process_video(video_request: VideoRequest):
    script = video_request.script
    image_style = ""

    audio_path = "./test/audio.mp3"
    script_to_speech_using_replicate(
        script, audio_path)
    
    subtitles,subtitles_segment = generate_subtitles_from_audio(audio_path)

    subtitles_time_series = split_time_series(subtitles_segment)

    subtitle_with_image_index,image_prompts = get_subtitle_with_image_index(subtitles_time_series)

    audio = AudioFileClip(audio_path)
    # Define subtitles
    duration = audio.duration

    background_images = prompts_to_images(image_prompts, image_style)

    video = VideoClip(lambda t: make_frame(t, background_images,subtitles,subtitle_with_image_index), duration=duration)
    video = video.set_audio(audio)

    # Export video
    video.write_videofile(f"output_video_{str(round(time.time()))}.mp4", fps=30, codec="libx264")
