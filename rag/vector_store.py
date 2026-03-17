from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance


COLLECTION = "snow_scripts"

client = QdrantClient(path="rag/vector_db")


def init_vector_db():

    collections = [c.name for c in client.get_collections().collections]

    if COLLECTION not in collections:

        print("Creating vector collection...")

        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(
                size=384,
                distance=Distance.COSINE
            )
        )

    else:

        print("Vector collection already exists.")