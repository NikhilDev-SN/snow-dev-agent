import random

from llm.openai_provider import generate_openai
from llm.gemini_provider import generate_gemini
from llm.claude_provider import generate_claude


class ModelRouter:

    def __init__(self, settings):
        self.settings = settings

        self.providers = {
            "openai": generate_openai,
            "gemini": generate_gemini,
            "claude": generate_claude
        }

    def get_random_key(self, provider):
        keys = getattr(self.settings, f"{provider.upper()}_API_KEYS", [])

        if not keys:
            raise Exception(f"No API keys configured for provider: {provider}")

        return random.choice(keys)

    def generate(self, messages, provider="openai"):

        errors = []

        # Try selected provider first, fallback to others
        providers_to_try = [provider] + [p for p in self.providers if p != provider]

        for p in providers_to_try:
            try:
                api_key = self.get_random_key(p)
                return self.providers[p](messages, api_key)

            except Exception as e:
                errors.append(f"{p}: {str(e)}")

        raise Exception("All providers failed: " + " | ".join(errors))