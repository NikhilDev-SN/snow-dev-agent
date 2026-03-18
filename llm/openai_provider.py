from openai import OpenAI


def generate_openai(messages, api_key):

    try:
        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # fast + cheap + stable
            messages=messages,
            temperature=0.2
        )

        return response.choices[0].message.content

    except Exception as e:
        raise Exception(f"OpenAI error: {str(e)}")