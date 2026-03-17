import json

from agent.schema import Artifact
from rag.retriever import retrieve_context
from llm.provider_router import ModelRouter

router = ModelRouter()


SYSTEM_PROMPT = """
You are a senior ServiceNow developer.

Generate production-ready ServiceNow scripts.

Supported artifacts:
- business_rule
- script_include
- client_script

Return valid JSON only.

Example schema:

{
 "artifact_type": "",
 "name": "",
 "table": "",
 "when": "",
 "insert": true,
 "update": true,
 "type": "",
 "script": ""
}
"""


def generate_script(requirement, provider=None):

    context = retrieve_context(requirement)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": f"Relevant ServiceNow scripts:\n{context}"},
        {"role": "user", "content": requirement}
    ]

    content = router.generate(messages, provider)

    data = json.loads(content)

    return Artifact(**data)