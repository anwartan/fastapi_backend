BASE_URL = "http://127.0.0.1:8000"

def generate_image_url(filename: str):
    return f"{BASE_URL}/media/{filename}"