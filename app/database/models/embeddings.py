from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.db import Base
from app.settings import settings


class EmbeddingsTable(Base):
    __tablename__ = "embeddings"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    content: Mapped[str] = mapped_column(Text())
    file_id: Mapped[str] = mapped_column(String)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, name="metadata")
    embeddings: Mapped[list[float]] = mapped_column(
        Vector(dim=settings.vector_dimensions)
    )
