import logging

from fastapi import HTTPException, status
from litellm import acompletion
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.constants import MESSAGES_ROLES
from app.database.models.chats import ChatsTable
from app.database.models.files import FilesTable
from app.database.models.message import MessagesTable
from app.schemas.chat_schema import InitChatReqSchema
from app.services.ask_service import ask_service
from app.settings import settings
from app.utils import get_id, make_chat_title

logger = logging.getLogger(__name__)

CHAT_SYSTEM_PROMPT = (
    "You are an AI assistant having a conversation with a user about a PDF document. "
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


class ChatService:
    async def init_chat(self, data: InitChatReqSchema, db: AsyncSession):
        result = await db.execute(
            select(FilesTable).where(FilesTable.id == data.file_id)
        )

        file = result.scalars().first()

        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
            )

        new_chat = ChatsTable(
            id=get_id(),
            client_id="change_this_later",
            title=make_chat_title(data.query),
            file_id=file.id,
            messages=[],
            file=file,
        )

        new_message = MessagesTable(
            id=get_id(),
            chat_id=new_chat.id,
            content=data.query,
            role=MESSAGES_ROLES["user"],
            order=1,
            chat=new_chat,
        )

        db.add(new_chat)
        db.add(new_message)
        await db.commit()

        return new_chat, new_message

    async def get_all_chats(self, db: AsyncSession):
        result = await db.execute(
            select(ChatsTable)
            .options(joinedload(ChatsTable.file))
            .order_by(ChatsTable.created_at.desc())
        )
        return result.scalars().all()

    async def get_chat_by_id(self, chat_id: str, db: AsyncSession):
        result = await db.execute(
            select(ChatsTable)
            .options(
                joinedload(ChatsTable.file),
                joinedload(ChatsTable.messages),
            )
            .where(ChatsTable.id == chat_id)
        )
        chat = result.scalars().first()

        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
            )
        # TODO: check how to do this in the database query itself
        chat.messages.sort(key=lambda m: m.order)

        return chat

    async def get_chat(self, chat_id: str, db: AsyncSession):
        result = await db.execute(select(ChatsTable).where(ChatsTable.id == chat_id))

        chat = result.scalars().first()

        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
            )

        return chat

    async def get_messages(self, chat_id: str, db: AsyncSession):
        result = await db.execute(
            select(MessagesTable)
            .where(MessagesTable.chat_id == chat_id)
            .order_by(MessagesTable.order)
        )

        return list(result.scalars().all())

    async def add_user_message(
        self,
        chat: ChatsTable,
        messages: list[MessagesTable],
        content: str,
        db: AsyncSession,
    ):
        new_message = MessagesTable(
            id=get_id(),
            chat_id=chat.id,
            content=content,
            role=MESSAGES_ROLES["user"],
            order=messages[-1].order + 1 if messages else 1,
            chat=chat,
        )
        db.add(new_message)
        await db.commit()

        return new_message

    def _retrieval_query(self, messages: list[MessagesTable]):
        # A follow-up like "what about the second one?" retrieves poorly on its
        # own, so the previous user question is embedded together with it.
        user_messages = [
            m.content for m in messages if m.role == MESSAGES_ROLES["user"]
        ]

        return "\n".join(user_messages[-2:])

    async def stream_reply(
        self,
        chat: ChatsTable,
        messages: list[MessagesTable],
        db: AsyncSession,
        announce_chat: bool = False,
    ):
        """Streams the AI reply to the last message in `messages` as SSE.

        Events: `chat` (the chat id, when `announce_chat`), unnamed `data` chunks,
        `error` (nothing is saved, so the reply can be retried) and `[DONE]`.
        """
        ai_order = messages[-1].order + 1
        retrieval_query = self._retrieval_query(messages)
        history = [
            {
                "role": "user" if m.role == MESSAGES_ROLES["user"] else "assistant",
                "content": m.content,
            }
            for m in messages
        ]

        if announce_chat:
            yield sse_event(chat.id, event="chat")

        full_reply = ""
        failed = False

        try:
            similar_docs = await ask_service.search_similar_docs(
                file_id=chat.file_id, query=retrieval_query, db=db
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
                    full_reply += content
                    yield sse_event(content)

            failed = not full_reply
        except Exception:
            logger.exception("Failed to stream reply for chat %s", chat.id)
            failed = True
        finally:
            # Also runs when the client disconnects mid-stream, keeping what streamed
            if full_reply and not failed:
                db.add(
                    MessagesTable(
                        id=get_id(),
                        chat_id=chat.id,
                        content=full_reply,
                        role=MESSAGES_ROLES["ai"],
                        order=ai_order,
                        chat=chat,
                    )
                )
                await db.commit()

        if failed:
            yield sse_event("Couldn't get a reply", event="error")
        else:
            yield "data: [DONE]\n\n"


chat_service = ChatService()
