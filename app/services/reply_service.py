import logging

from fastapi import HTTPException, status
from litellm import acompletion
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import MESSAGES_ROLES
from app.database.models.files import FilesTable
from app.schemas.reply_schema import ReplyRequestSchema
from app.services.ask_service import ask_service
from app.settings import settings

logger = logging.getLogger(__name__)

CHAT_SYSTEM_PROMPT = (
    "You are an AI assistant having a conversation with a user about a book. "
    "Answer the user's questions based ONLY on the document context below. "
    "Use the earlier messages in the conversation to understand follow-up questions.\n\n"
    "Rules:\n"
    "1. Never use knowledge from outside the context, and do not guess.\n"
    "2. If the answer is not contained in the context, say exactly: "
    "'I cannot find the answer in the provided document.'\n"
    "3. Answer naturally and clearly. Use Markdown when it helps readability.\n\n"
    "Document context:\n{context}"
)


def sse_event(data: str, event: str | None = None):
    escaped = data.replace("\\", "\\\\").replace("\n", "\\n")
    prefix = f"event: {event}\n" if event else ""

    return f"{prefix}data: {escaped}\n\n"


class ReplyService:
    async def validate(self, data: ReplyRequestSchema, db: AsyncSession):
        if data.messages[-1].role != MESSAGES_ROLES["user"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The last message must be from the user",
            )

        result = await db.execute(
            select(FilesTable.id).where(FilesTable.id == data.file_id)
        )

        if not result.first():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
            )

    def _retrieval_query(self, data: ReplyRequestSchema):
        # A follow-up like "what about the second one?" retrieves poorly on its
        # own, so the previous user question is embedded together with it.
        user_messages = [
            m.content for m in data.messages if m.role == MESSAGES_ROLES["user"]
        ]

        return "\n".join(user_messages[-2:])

    async def stream_reply(self, data: ReplyRequestSchema, db: AsyncSession):
        """Streams the AI reply to the last message in `data.messages` as SSE.

        Events: unnamed `data` chunks, `error` and `[DONE]`. Nothing is stored.
        """
        history = [
            {
                "role": "user" if m.role == MESSAGES_ROLES["user"] else "assistant",
                "content": m.content,
            }
            for m in data.messages
        ]

        has_reply = False

        try:
            similar_docs = await ask_service.search_similar_docs(
                file_id=data.file_id, query=self._retrieval_query(data), db=db
            )
            context = "\n\n---\n\n".join(similar_docs)

            response = await acompletion(
                model=settings.llm_model,
                api_key=settings.llm_api_key,
                api_base=settings.llm_api_base,
                api_version=None,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
                messages=[
                    {
                        "role": "system",
                        "content": CHAT_SYSTEM_PROMPT.format(context=context),
                    },
                    *history,
                ],
                stream=True,
            )

            async for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    has_reply = True
                    yield sse_event(content)
        except Exception:
            logger.exception("Failed to stream reply for file %s", data.file_id)
            has_reply = False

        if has_reply:
            yield "data: [DONE]\n\n"
        else:
            yield sse_event("Couldn't get a reply", event="error")


reply_service = ReplyService()
