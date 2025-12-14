import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MOVIE_EMBED_PATH = os.getenv("MOVIE_EMBED_PATH")
USER_EMBED_PATH = os.getenv("USER_EMBED_PATH")


TOP_K = 20
FINAL_K = 5


