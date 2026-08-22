import litellm
from fastapi import HTTPException, status
from langchain_huggingface import HuggingFaceEmbeddings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import EmbeddingsTable, FilesTable
from app.schemas.api_response import ResponseSchema
from app.schemas.ask import AskRequestSchema
from app.settings import settings


class AskService:
    async def _get_file_by_id(self, file_id: str, db: AsyncSession) -> FilesTable:
        result = await db.execute(select(FilesTable).where(FilesTable.id == file_id))

        file = result.scalars().first()

        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File with id {file_id} doesn't exist.",
            )

        return file

    async def _search_similar_docs(self, file_id: str, query: str, db: AsyncSession):
        embedding_model = HuggingFaceEmbeddings(model_name=settings.embedding_model)

        query_vector = embedding_model.embed_query(query)

        result = await db.execute(
            select(EmbeddingsTable.content)
            .where(EmbeddingsTable.file_id == file_id)
            .order_by(EmbeddingsTable.embeddings.cosine_distance(query_vector))
            .limit(5)
        )

        similar_docs = result.scalars().all()

        return similar_docs

    async def _ask_llm(self, query: str, context: str):

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an assistant answering questions based on the provided context.\n\n"
                    f"Context:\n f{context}"
                ),
            },
            {"role": "user", "content": query},
        ]

        response = await litellm.acompletion(
            model=settings.llm_model,
            api_key=settings.llm_api_key,
            api_base=settings.llm_api_base,
            api_version=None,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            messages=messages,
        )

        return response.choices[0].message.content

    async def ask_question(self, data: AskRequestSchema, db: AsyncSession):
        file = await self._get_file_by_id(file_id=data.file_id, db=db)

        similar_content = await self._search_similar_docs(
            file_id=file.id, query=data.query, db=db
        )

        formatted_context = "\n\n---\n\n".join(similar_content)

        result = await self._ask_llm(query=data.query, context=formatted_context)

        return ResponseSchema(
            status=True,
            data={
                "query": data.query,
                "answer": result,
            },
        )


ask_service = AskService()
