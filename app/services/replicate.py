import replicate
from app.config.settings import REPLICATE_API_TOKEN
from io import BytesIO
from PIL import Image

client = replicate.Client(api_token=REPLICATE_API_TOKEN)
def generate_audio(script, speed=0.9, voice="am_adam"):
    print("Generating speech...")
    output = client.run(
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
    
def generate_image(prompt,index=0,count=0):
    if count:
        print(f"->processing {index+1} image of {count}...")
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
            if count:
                print(f"->completed !!!")
            return image
        else:
            print("Unexpected output format.")
            return None
    else:
        print("Invalid response from Replicate API.")
        return None


