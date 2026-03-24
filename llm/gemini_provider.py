from google import genai


def generate_gemini(messages, api_key):
    try:
        client = genai.Client(api_key=api_key)

        safe_messages = []

        for m in messages:
            if isinstance(m, dict):
                safe_messages.append(m)
            elif isinstance(m, list):
                for inner in m:
                    if isinstance(inner, dict):
                        safe_messages.append(inner)
            else:
                safe_messages.append({
                    "role": "user",
                    "content": str(m)
                })

        prompt = "\n\n".join([
            f"{m.get('role', 'user').upper()}:\n{m.get('content', '')}"
            for m in safe_messages
        ])

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return response.text.strip()

    except Exception as e:
        raise Exception(f"Gemini error: {str(e)}")