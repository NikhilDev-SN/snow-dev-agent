import os
from dotenv import load_dotenv

load_dotenv()


def parse_keys(key_string):
    if not key_string:
        return []
    return [k.strip() for k in key_string.split(",") if k.strip()]


class Settings:

    # 🔥 MULTI-KEY SUPPORT
    OPENAI_API_KEYS = parse_keys(os.getenv("OPENAI_API_KEYS"))
    GEMINI_API_KEYS = parse_keys(os.getenv("GEMINI_API_KEYS"))
    CLAUDE_API_KEYS = parse_keys(os.getenv("CLAUDE_API_KEYS"))

    DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "openai")

    # ServiceNow
    SN_INSTANCE = os.getenv("SN_INSTANCE")
    SN_USERNAME = os.getenv("SN_USERNAME")
    SN_PASSWORD = os.getenv("SN_PASSWORD")

    SN_CLIENT_ID = os.getenv("SN_CLIENT_ID")
    SN_CLIENT_SECRET = os.getenv("SN_CLIENT_SECRET")


settings = Settings()