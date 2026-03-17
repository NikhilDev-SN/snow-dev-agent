import sys
import os

# Allow imports from project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import requests
from sentence_transformers import SentenceTransformer
from qdrant_client.models import PointStruct

from config.settings import settings
from integration.servicenow_client import get_oauth_token
from rag.vector_store import client, init_vector_db, COLLECTION


model = SentenceTransformer("all-MiniLM-L6-v2")


def fetch_table(table):

    token = get_oauth_token()

    headers = {
        "Authorization": f"Bearer {token}"
    }

    url = f"{settings.SN_INSTANCE}/api/now/table/{table}"

    params = {
        "sysparm_limit": 100,
        "sysparm_fields": "name,script"
    }

    print(f"Fetching {table}...")

    r = requests.get(url, headers=headers, params=params)

    if r.status_code != 200:
        raise Exception(f"Failed to fetch {table}: {r.text}")

    return r.json()["result"]


def index_scripts():

    print("Initializing vector database...")

    init_vector_db()

    tables = [
        "sys_script_include",
        "sys_script",
        "sys_script_client"
    ]

    points = []

    idx = 0

    for table in tables:

        records = fetch_table(table)

        print(f"{len(records)} records retrieved")

        for rec in records:

            name = rec.get("name", "")
            script = rec.get("script", "")

            if not script:
                continue

            text = f"{name}\n{script}"

            vector = model.encode(text).tolist()

            points.append(
                PointStruct(
                    id=idx,
                    vector=vector,
                    payload={
                        "table": table,
                        "name": name,
                        "content": text
                    }
                )
            )

            idx += 1

    print("Uploading vectors to Qdrant...")

    client.upsert(
        collection_name=COLLECTION,
        points=points
    )

    print(f"Indexed scripts: {len(points)}")

    # Close vector DB cleanly
    client.close()


if __name__ == "__main__":

    index_scripts()