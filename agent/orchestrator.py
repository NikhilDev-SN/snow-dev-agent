from llm.router import ModelRouter
from config.settings import settings
import json
import re

router = ModelRouter(settings)


# ---------------- CLEAN RESPONSE ----------------
def extract_json(text):
    """
    Extract JSON from LLM response (handles ```json blocks)
    """

    if not text:
        return None

    # 🔥 Remove markdown ```json ... ```
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```", "", text)

    text = text.strip()

    # 🔥 Extract JSON block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)

    return text


# ---------------- NORMALIZE TYPE ----------------
def normalize_artifact_type(value):
    if not value:
        return "unknown"

    value = value.lower().strip()

    mapping = {
        "script include": "script_include",
        "script_include": "script_include",

        "business rule": "business_rule",
        "business_rule": "business_rule",

        "client script": "client_script",
        "client_script": "client_script",
    }

    return mapping.get(value, "unknown")


# ---------------- MAIN FUNCTION ----------------
def generate_script(requirement, provider="gemini", context="", artifact_hint="auto"):

    messages = [
        {
            "role": "system",
            "content": "You are a ServiceNow expert developer."
        },
        {
            "role": "user",
            "content": f"""
Use the context below to generate a valid ServiceNow script.

Context:
{context}

Requirement:
{requirement}

Instructions:
- Identify correct artifact type
- Generate production-ready script
- Follow best practices
- IMPORTANT: Do NOT wrap output in markdown
- IMPORTANT: Return ONLY raw JSON

Return artifact_type ONLY as:
- business_rule
- script_include
- client_script

Output STRICT JSON:
{{
  "artifact_type": "",
  "name": "",
  "script": ""
}}
"""
        }
    ]

    response = router.generate(messages, provider=provider)

    print("\n[RAW LLM RESPONSE]\n", response)

    try:
        # 🔥 CLEAN RESPONSE FIRST
        cleaned = extract_json(response)

        print("\n[CLEANED JSON]\n", cleaned)

        data = json.loads(cleaned)

        # 🔥 Normalize type
        data["artifact_type"] = normalize_artifact_type(
            data.get("artifact_type")
        )

        return data

    except Exception as e:
        print("\n[JSON ERROR]\n", str(e))

        return {
            "artifact_type": "unknown",
            "name": "generated_script",
            "script": response
        }