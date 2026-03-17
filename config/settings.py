import os
from dotenv import load_dotenv

load_dotenv()

class Settings:

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    SN_INSTANCE = os.getenv("SN_INSTANCE")

    SN_CLIENT_ID = os.getenv("SN_CLIENT_ID")
    SN_CLIENT_SECRET = os.getenv("SN_CLIENT_SECRET")

settings = Settings()