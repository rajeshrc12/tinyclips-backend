import numpy as np
from PIL import ImageDraw, ImageFont


def get_prompt_by_time(result, time):
    if not result or not isinstance(result, list):
        return 0  # Default to first index if result is invalid

    return next(
        (entry['index']
         for entry in result if entry['start'] <= time <= entry['end']),
        min(len(result) - 1, len(result) - 1)  # Ensure the index is in range
    )


def make_frame(t, background_images, subtitles, subtitle_with_image_index):
    image_index = get_prompt_by_time(subtitle_with_image_index, t)

    # Ensure index is within range
    if not (0 <= image_index < len(background_images)):
        image_index = max(0, len(background_images) -
                          1)  # Set to last valid index

    base_image = background_images[image_index].copy()
    draw = ImageDraw.Draw(base_image)

    current_word = next(
        (subtitle['word']
         for subtitle in subtitles if subtitle['start'] <= t < subtitle['end']),
        ""
    )

    font = ImageFont.truetype("app/static/fonts/eng.ttf", 60)
    text_width, text_height = draw.textbbox(
        (0, 0), current_word, font=font)[2:]
    text_x = (base_image.width - text_width) // 2
    text_y = (base_image.height - text_height) // 2

    draw.text((text_x, text_y), current_word, font=font,
              fill="white", stroke_width=5, stroke_fill="black")
    return np.array(base_image)
