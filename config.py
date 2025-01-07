import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    ONE_RING_TOKEN = os.getenv('ONE_RING_TOKEN')
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    GOOGLE_CX_KEY = os.getenv('GOOGLE_CX_KEY')
    API_NINJA_API_KEY = os.getenv('API_NINJA_API_KEY')
    OPENAI_API_KEY = os.getenv('OPEN_AI_API_KEY')
    DATABASE_PATH = 'responses.db'
    VERSION = '1.0.0'
    ONE_RING_HEADERS = {
        "Authorization": f"Bearer {os.getenv('ONE_RING_TOKEN')}"
    }