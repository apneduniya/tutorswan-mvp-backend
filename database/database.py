import os
from dotenv import load_dotenv


load_dotenv()

MONGO_CONNECTION_URL = os.environ.get("MONGO_CONNECTION_URL")
DATABASE_NAME = os.environ.get("DATABASE_NAME")
IMGBB_API_KEY = os.environ.get("IMGBB_API_KEY")
