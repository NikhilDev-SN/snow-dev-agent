import requests
from config.settings import settings
from datetime import datetime, timezone
from pathlib import Path
import json

ARTIFACT_TABLES = {
    "business_rule": "sys_script",
    "script_include": "sys_script_include",
    "client_script": "sys_script_client",
}

DEBUG_LOG_PATH = Path(__file__).resolve().parents[1] / "logs" / "deployment_debug.txt"


def write_debug_log(event, details):
    try:
        DEBUG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).isoformat()
        payload = json.dumps(details, ensure_ascii=True, default=str)

        with DEBUG_LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(f"[{timestamp}] {event} {payload}\n")
    except Exception:
        pass


def truncate(text, limit=1000):
    if text is None:
        return ""
    text = str(text)
    if len(text) <= limit:
        return text
    return text[:limit] + "...[truncated]"


def summarize_artifact_for_log(artifact):
    if not isinstance(artifact, dict):
        return {"artifact_repr": truncate(artifact, 500)}

    script = artifact.get("script", "")

    return {
        "artifact_type": artifact.get("artifact_type"),
        "requested_artifact_type": artifact.get("requested_artifact_type"),
        "name": artifact.get("name"),
        "table": artifact.get("table"),
        "requested_table": artifact.get("requested_table"),
        "when": artifact.get("when"),
        "insert": artifact.get("insert"),
        "update": artifact.get("update"),
        "type": artifact.get("type"),
        "script_length": len(script) if isinstance(script, str) else None,
    }


def normalize_artifact_type(value):
    if not value:
        return "unknown"

    value = str(value).lower().strip()

    mapping = {
        "business rule": "business_rule",
        "business_rule": "business_rule",
        "script include": "script_include",
        "script_include": "script_include",
        "client script": "client_script",
        "client_script": "client_script",
    }

    return mapping.get(value, "unknown")


def coerce_bool(value, default=False):
    if value is None:
        return default

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}

    return bool(value)


def resolve_target_table(artifact_type):
    target_table = ARTIFACT_TABLES.get(normalize_artifact_type(artifact_type))

    if not target_table:
        raise ValueError(f"Unsupported artifact type: {artifact_type}")

    return target_table


def build_payload(artifact):
    artifact_type = normalize_artifact_type(
        artifact.get("artifact_type") or artifact.get("requested_artifact_type")
    )

    table = resolve_target_table(artifact_type)

    body = {
        "name": artifact.get("name") or "generated_script",
        "script": artifact.get("script") or "",
        "active": True,
    }

    if artifact_type == "business_rule":
        target_table = artifact.get("table") or artifact.get("requested_table")

        if not target_table:
            raise ValueError("Business rules require a target table")

        body.update({
            "collection": target_table,
            "when": (artifact.get("when") or "after").strip().lower(),
            "insert": coerce_bool(artifact.get("insert"), True),
            "update": coerce_bool(artifact.get("update"), True),
            "advanced": True,
        })

        if artifact.get("order") is not None:
            body["order"] = artifact.get("order")

    elif artifact_type == "client_script":
        target_table = artifact.get("table") or artifact.get("requested_table")

        if not target_table:
            raise ValueError("Client scripts require a target table")

        body["table"] = target_table

        if artifact.get("type"):
            body["type"] = artifact.get("type")

    elif artifact_type == "script_include":
        pass

    return table, body


def send_with_fallback(url, headers, payload_candidates):
    errors = []

    for index, payload in enumerate(payload_candidates, start=1):
        write_debug_log(
            "deploy_attempt",
            {
                "attempt": index,
                "url": url,
                "target_table": payload.get("collection") or payload.get("table"),
                "payload_keys": sorted(payload.keys()),
            },
        )

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()

            write_debug_log(
                "deploy_success",
                {
                    "attempt": index,
                    "status_code": response.status_code,
                    "response": truncate(response.text, 2000),
                },
            )

            return response
        except requests.RequestException as exc:
            response = getattr(exc, "response", None)
            error_text = truncate(response.text if response is not None else str(exc), 2000)

            write_debug_log(
                "deploy_failure",
                {
                    "attempt": index,
                    "status_code": getattr(response, "status_code", None),
                    "response": error_text,
                },
            )

            errors.append(error_text)

    raise RuntimeError("ServiceNow deploy failed: " + " | ".join(errors))


# ---------------- TOKEN ----------------
def get_oauth_token():

    instance = (settings.SN_INSTANCE or "").rstrip("/")

    if not instance:
        raise ValueError("SN_INSTANCE is not configured")

    url = f"{instance}/oauth_token.do"

    data = {
        "grant_type": "client_credentials",
        "client_id": settings.SN_CLIENT_ID,
        "client_secret": settings.SN_CLIENT_SECRET
    }

    r = requests.post(
        url,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    print("\n[OAUTH RESPONSE]", r.text)

    try:
        r.raise_for_status()
    except requests.RequestException as exc:
        write_debug_log(
            "oauth_failure",
            {
                "status_code": r.status_code,
                "response": truncate(r.text, 2000),
            },
        )
        raise RuntimeError(f"ServiceNow OAuth failed: {r.status_code} {truncate(r.text, 500)}") from exc

    write_debug_log(
        "oauth_success",
        {
            "status_code": r.status_code,
            "content_type": r.headers.get("Content-Type"),
            "response_preview": truncate(r.text, 500),
        },
    )

    if "Instance Hibernating page" in r.text:
        write_debug_log(
            "oauth_hibernating",
            {
                "status_code": r.status_code,
                "content_type": r.headers.get("Content-Type"),
                "response": truncate(r.text, 2000),
            },
        )
        raise RuntimeError(
            "ServiceNow instance is hibernating. Wake the instance and retry the deployment."
        )

    try:
        return r.json().get("access_token")
    except ValueError as exc:
        write_debug_log(
            "oauth_invalid_json",
            {
                "status_code": r.status_code,
                "content_type": r.headers.get("Content-Type"),
                "response": truncate(r.text, 2000),
            },
        )
        raise RuntimeError("ServiceNow OAuth returned a non-JSON response") from exc


# ---------------- HEADERS ----------------
def get_headers():

    token = get_oauth_token()

    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }


# ---------------- DEPLOY ----------------
def deploy_artifact(artifact):

    try:
        instance = (settings.SN_INSTANCE or "").rstrip("/")

        if not instance:
            raise ValueError("SN_INSTANCE is not configured")

        table, body = build_payload(artifact)

        headers = get_headers()

        url = f"{instance}/api/now/table/{table}"

        payload_candidates = [body]

        if normalize_artifact_type(artifact.get("artifact_type")) == "business_rule":
            fallback = dict(body)
            fallback["table"] = fallback.pop("collection")
            payload_candidates.append(fallback)

        response = send_with_fallback(url, headers, payload_candidates)

        print("\n[SN RESPONSE]", response.text)

        try:
            return response.json()
        except ValueError:
            write_debug_log(
                "deploy_non_json_response",
                {
                    "status_code": response.status_code,
                    "content_type": response.headers.get("Content-Type"),
                    "response": truncate(response.text, 2000),
                },
            )
            return {
                "status_code": response.status_code,
                "content_type": response.headers.get("Content-Type"),
                "response_text": truncate(response.text, 2000),
            }
    except Exception as exc:
        write_debug_log(
            "deploy_artifact_exception",
            {
                "artifact": summarize_artifact_for_log(artifact),
                "error": truncate(str(exc), 2000),
            },
        )
        raise
