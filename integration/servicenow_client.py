import requests
from config.settings import settings


def get_oauth_token():

    url = f"{settings.SN_INSTANCE}/oauth_token.do"

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

    r.raise_for_status()

    return r.json()["access_token"]


def get_headers():

    token = get_oauth_token()

    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }


def deploy_artifact(artifact):

    artifact_type = artifact["artifact_type"].lower()

    if artifact_type == "business_rule":

        table = "sys_script"

        body = {
            "name": artifact["name"],
            "collection": artifact["table"],
            "when": artifact.get("when", "before"),
            "insert": artifact.get("insert", True),
            "update": artifact.get("update", False),
            "script": artifact["script"],
            "active": True,
            "advanced": True
        }

    elif artifact_type == "script_include":

        table = "sys_script_include"

        body = {
            "name": artifact["name"],
            "script": artifact["script"],
            "active": True
        }

    elif artifact_type == "client_script":

        table = "sys_script_client"

        body = {
            "name": artifact["name"],
            "table": artifact["table"],
            "type": artifact.get("type", "onChange"),
            "script": artifact["script"],
            "active": True
        }

    else:

        raise Exception("Unsupported artifact type")

    url = f"{settings.SN_INSTANCE}/api/now/table/{table}"

    r = requests.post(url, headers=get_headers(), json=body)

    try:
        return r.json()
    except:
        return {"status_code": r.status_code}