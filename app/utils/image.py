from PIL import ImageDraw, ImageFont
import numpy as np

def create_new_image_prompt(prompt,image_style):
    new_prompt = prompt
    if image_style:
        new_prompt = f"Create {image_style} style image of " + prompt
    return new_prompt

def get_prompt_by_time(result, time):
    for entry in result:
        if entry['start'] <= time < entry['end']:
            return entry['index']
    return len(result)-1

def make_frame(t,image_objects,subtitles,subtitle_with_image_index):
    image_index = get_prompt_by_time(subtitle_with_image_index,t)
    base_image = image_objects[image_index].copy()
    draw = ImageDraw.Draw(base_image)

    current_word = next((subtitle['word'] for subtitle in subtitles if subtitle['start'] <= t < subtitle['end']), "")

    font = ImageFont.truetype("app/static/fonts/eng.ttf", 70)
    text_width, text_height = draw.textbbox((0, 0), current_word, font=font)[2:]
    text_x = (base_image.width - text_width) // 2
    text_y = (base_image.height - text_height) // 2

    draw.text((text_x, text_y), current_word, font=font, fill="white",stroke_width=5, stroke_fill="black")
    return np.array(base_image)
