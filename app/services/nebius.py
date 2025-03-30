import json
from openai import OpenAI
from app.config.settings import NEBIUS_API_KEY
import requests
from io import BytesIO
from PIL import Image

client = OpenAI(
    base_url="https://api.studio.nebius.com/v1/",
    api_key=NEBIUS_API_KEY
)


def create_image_prompts(main_script, sub_script, image_count, image_style):
    print("Generating prompts from script...")
    script_template = f"""
Read and thoroughly understand the following Main Script to grasp its full context:
Main Script:
"{main_script}"

Now, analyze the Sub-Script, which is a part of the Main Script. Your task is to generate total {image_count} relevant and visually compelling {image_style} style portrait image prompt that aligns with Sub-Script.
Accurately depict the scene, emotions, facial expressions, and overall atmosphere.
If the Sub-Script references a product, service, or advertisement then add appropriate text, symbols, or objects to blend seamlessly into the environment.
Primary focus should be on the Sub-Script when generating the prompts, ensuring relevance and coherence.

Sub-Script:
"{sub_script}"

Return array of prompts with valid JSON format, so I can parse without error.
[
"First prompt description",
"Second prompt description",
...
"Last prompt description"
]

In response ensure there are no extra keys, indices, or labels.
    """
    try:
        # Generate the response from the model
        # response = gemini_model.generate_content(script_template).text
        # print("\n", response, "\n")

        # Extract the string between the brackets and strip any leading or trailing whitespace
        # prompts = json.loads("["+cleaned_response+"]")
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3",
            max_tokens=512,
            temperature=0.3,
            top_p=0.95,
            messages=[
                {
                    "role": "system",
                    "content": script_template
                }
            ]
        )
        content = json.loads(response.choices[0].message.content)
        print("Prompts generated successfully.")
        return content
    except Exception as e:
        print("**************Prompt generation error*************", str(e))
        return []


def generate_image(prompt):
    print("generating image...")
    response = client.images.generate(
        model="black-forest-labs/flux-schnell",
        response_format="url",
        extra_body={
            "response_extension": "png",
            "width": 576,
            "height": 1024,
            "num_inference_steps": 4,
            "negative_prompt": "Distorted body, extra limbs, missing fingers, deformed face, incorrect spelling, gibberish text, extra fingers, disembodied head.",
            "seed": -1
        },
        prompt=prompt
    )
    # Ensure response is parsed as JSON
    # Convert JSON string to dictionary
    data = json.loads(response.to_json())

    # Extract the image URL
    url = data["data"][0]["url"]

    # Fetch and open the image
    response = requests.get(url)
    response.raise_for_status()  # Ensure we got a valid response

    # Convert to Pillow Image object
    image = Image.open(BytesIO(response.content))
    print("generating completed!!!")
    return image
    # return Image.new("RGB", (1080, 1920), (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
