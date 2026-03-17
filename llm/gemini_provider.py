from google.genai import Client


def generate_gemini(messages, api_key):

    client = Client(api_key=api_key)

    prompt = "\n".join([m["content"] for m in messages])

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    return response.text