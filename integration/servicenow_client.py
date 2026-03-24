import requests
from config.settings import settings


# ---------------- NORMALIZATION ----------------
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


# ---------------- SAFE RESPONSE PARSER ----------------
def safe_json_response(response):
    try:
        return response.json()
    except Exception:
        return {
            "status_code": response.status_code,
            "text": response.text
        }


# ---------------- HEADERS ----------------
def get_headers():
    return {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }


# ---------------- DEPLOY ----------------
def deploy_artifact(artifact):

    artifact_type = normalize_artifact_type(
        artifact.get("artifact_type")
    )

    name = artifact.get("name", "Generated Artifact")
    script = artifact.get("script", "")

    if not script:
        raise Exception("Script content is empty")

    # ---------------- BUSINESS RULE ----------------
    if artifact_type == "business_rule":

        table = "sys_script"

        body = {
            "name": name,
            "collection": artifact.get("table", "incident"),
            "when": artifact.get("when", "before"),
            "insert": artifact.get("insert", True),
            "update": artifact.get("update", False),
            "script": script,
            "active": True,
            "advanced": True
        }

    # ---------------- SCRIPT INCLUDE ----------------
    elif artifact_type == "script_include":

        table = "sys_script_include"

        body = {
            "name": name,
            "script": script,
            "active": True
        }

    # ---------------- CLIENT SCRIPT ----------------
    elif artifact_type == "client_script":

        table = "sys_script_client"

        body = {
            "name": name,
            "table": artifact.get("table", "incident"),
            "type": artifact.get("type", "onChange"),
            "script": script,
            "active": True
        }

    else:
        raise Exception(f"Unsupported artifact type: {artifact_type}")

    url = f"{settings.SN_INSTANCE}/api/now/table/{table}"

    print("\n========== SERVICE NOW REQUEST ==========")
    print("URL:", url)
    print("TYPE:", artifact_type)
    print("BODY:", body)
    print("=========================================\n")

    try:
        r = requests.post(
            url,
            auth=(settings.SN_USERNAME, settings.SN_PASSWORD),  # 🔥 BASIC AUTH
            headers=get_headers(),
            json=body,
            timeout=30
        )
    except Exception as e:
        raise Exception(f"Request failed: {str(e)}")

    print("\n========== RAW RESPONSE ==========")
    print("STATUS:", r.status_code)
    print("HEADERS:", r.headers)
    print("TEXT:", r.text[:1000])
    print("=================================\n")

    result = safe_json_response(r)

    # 🔥 Handle HTTP errors clearly
    if not r.ok:
        raise Exception(f"ServiceNow API error: {result}")

    return result