import google.generativeai as genai
from app.config.settings import GEMINI_API_TOKEN
import json

genai.configure(api_key=GEMINI_API_TOKEN)
gemini_model = genai.GenerativeModel("gemini-2.0-flash")

def create_image_prompts(script,image_prompts_count):
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
