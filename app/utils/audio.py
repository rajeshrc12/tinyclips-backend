import requests
from io import BytesIO
from requests.exceptions import RequestException

def get_audio_in_bytes(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Ensure the request was successful
        audio = BytesIO(response.content)
        return audio
    except RequestException as e:
        print(f"Error fetching file from URL: {e}")
        return False