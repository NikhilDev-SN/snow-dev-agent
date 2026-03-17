import requests
from integration.servicenow_client import _headers
from config.settings import settings


def create_change_request(description):

    url = f"{settings.SN_INSTANCE}/api/now/table/change_request"

    body = {
        "short_description": description,
        "type": "normal",
        "category": "software"
    }

    r = requests.post(url, headers=_headers(), json=body)

    return r.json()