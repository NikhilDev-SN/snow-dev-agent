import anthropic


def generate_claude(messages, api_key):

    client = anthropic.Anthropic(api_key=api_key)

    prompt = "\n".join([m["content"] for m in messages])

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text