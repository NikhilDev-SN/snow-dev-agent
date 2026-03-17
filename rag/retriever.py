from sentence_transformers import SentenceTransformer
from rag.vector_store import client, COLLECTION

model = SentenceTransformer("all-MiniLM-L6-v2")


def retrieve_context(query, limit=5):

    # Convert query to vector embedding
    vector = model.encode(query).tolist()

    # Query Qdrant vector database
    response = client.query_points(
        collection_name=COLLECTION,
        query=vector,
        limit=limit
    )

    context = []

    for point in response.points:

        payload = point.payload or {}

        content = payload.get("content")

        if content:
            context.append(content)

    return "\n\n".join(context)