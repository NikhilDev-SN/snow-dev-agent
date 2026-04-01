from agent.prompts import build_prompt, build_table_inference_prompt
from agent.schema import Artifact
from config.settings import settings
from llm.router import ModelRouter
from pydantic import ValidationError
import json
import re
import os

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


def normalize_artifact_hint(value):
    if not value:
        return "auto"

    value = str(value).lower().strip()

    if value == "auto":
        return "auto"

    normalized = normalize_artifact_type(value)

    return normalized if normalized != "unknown" else "auto"


def artifact_requires_table(artifact_type):
    return artifact_type in {"business_rule", "client_script"}


def guess_table_from_text(*texts):
    combined = " ".join([str(text or "") for text in texts]).lower()

    patterns = [
        (r"\bincident(s)?\b", "incident"),
        (r"\bproblem(s)?\b", "problem"),
        (r"\bchange request(s)?\b", "change_request"),
        (r"\brequest(ed)? item(s)?\b", "sc_req_item"),
        (r"\bcatalog item request(s)?\b", "sc_req_item"),
        (r"\bsc_req_item\b", "sc_req_item"),
        (r"\buser(s)?\b", "sys_user"),
        (r"\bgroup(s)?\b", "sys_user_group"),
        (r"\bconfiguration item(s)?\b", "cmdb_ci"),
        (r"\bcmdb ci\b", "cmdb_ci"),
        (r"\btask(s)?\b", "task"),
        (r"\bu_[a-z0-9_]+\b", None),
    ]

    for pattern, table in patterns:
        if re.search(pattern, combined):
            if table is None:
                match = re.search(pattern, combined)
                return match.group(0) if match else None
            return table

    return None


def infer_missing_table(requirement, context, provider, artifact_type, artifact_name="", script=""):
    # Prefer deterministic hints first, then let the LLM repair the omission.
    hinted_table = guess_table_from_text(requirement, context, artifact_name, script)
    if hinted_table:
        return hinted_table

    repair_messages = [
        {
            "role": "system",
            "content": "You are a ServiceNow table inference assistant."
        },
        {
            "role": "user",
            "content": build_table_inference_prompt(
                requirement=requirement,
                context=context,
                artifact_type=artifact_type,
                name=artifact_name,
                script=script,
            ),
        }
    ]

    repair_response = router.generate(repair_messages, provider=provider)
    cleaned = extract_json(repair_response)

    try:
        data = json.loads(cleaned)
        table = data.get("table")
        if table and str(table).strip().lower() != "null":
            return str(table).strip()
    except Exception:
        pass

    return None


# ---------------- MAIN FUNCTION ----------------
def generate_script(
    requirement,
    provider="gemini",
    context="",
    artifact_hint="auto",
):
    requested_artifact_type = normalize_artifact_hint(artifact_hint)

    messages = [
        {
            "role": "system",
            "content": "You are a ServiceNow expert developer."
        },
        {
            "role": "user",
            "content": build_prompt(
                requirement=requirement,
                context=context,
                artifact_hint=requested_artifact_type,
            ),
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
        model_artifact_type = normalize_artifact_type(data.get("artifact_type"))

        if requested_artifact_type != "auto":
            if model_artifact_type != requested_artifact_type:
                print(
                    f"\n[ARTIFACT TYPE OVERRIDE]\n"
                    f"model={model_artifact_type} requested={requested_artifact_type}"
                )
            data["artifact_type"] = requested_artifact_type
        else:
            data["artifact_type"] = model_artifact_type

        if not data.get("name"):
            data["name"] = "generated_script"

        if artifact_requires_table(data.get("artifact_type")) and not data.get("table"):
            inferred_table = infer_missing_table(
                requirement=requirement,
                context=context,
                provider=provider,
                artifact_type=data.get("artifact_type"),
                artifact_name=data.get("name", ""),
                script=data.get("script", ""),
            )
            if inferred_table:
                data["table"] = inferred_table

        artifact = Artifact.model_validate(data)

        if artifact_requires_table(artifact.artifact_type) and not artifact.table:
            raise ValueError(
                "Could not infer a target table from the requirement. "
                "Please restate the requirement with the record type you want to target."
            )

        return artifact.model_dump()

    except ValidationError as e:
        print("\n[SCHEMA ERROR]\n", str(e))

        return {
            "artifact_type": requested_artifact_type if requested_artifact_type != "auto" else "unknown",
            "name": data.get("name", "generated_script") if "data" in locals() else "generated_script",
            "script": data.get("script", response) if "data" in locals() else response,
            "table": data.get("table") if "data" in locals() else None,
        }

    except Exception as e:
        print("\n[JSON ERROR]\n", str(e))

        return {
            "artifact_type": requested_artifact_type if requested_artifact_type != "auto" else "unknown",
            "name": "generated_script",
            "script": response
        }
