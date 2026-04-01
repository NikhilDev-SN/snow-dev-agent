import requests
from integration.servicenow_client import get_headers
from config.settings import settings


def create_change_request(description):

    instance = (settings.SN_INSTANCE or "").rstrip("/")

    if not instance:
        raise ValueError("SN_INSTANCE is not configured")

    url = f"{instance}/api/now/table/change_request"

    body = {
        "short_description": description,
        "type": "normal",
        "category": "software"
    }

    r = requests.post(url, headers=get_headers(), json=body)

    return r.json()
