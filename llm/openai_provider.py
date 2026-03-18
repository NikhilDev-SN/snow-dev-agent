import os
from openai import OpenAI


def generate_openai(messages, api_key):
    try:
        # 🔥 Prevent proxy issues (Render fix)
        os.environ.pop("HTTP_PROXY", None)
        os.environ.pop("HTTPS_PROXY", None)

        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.2,
        )

        return response.choices[0].message.content

    except Exception as e:
        raise Exception(f"OpenAI error: {str(e)}")