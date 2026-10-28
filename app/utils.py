from functools import cache
from uuid import uuid7

from app.settings import settings


def get_id():
    id = uuid7()

    return str(id)


@cache
def get_embedding_model():
    # Imported lazily so torch isn't loaded until the first embedding request.
    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(model_name=settings.embedding_model)
