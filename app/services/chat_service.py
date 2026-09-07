from typing import TypedDict

import socketio
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.constants import MESSAGES_ROLES
from app.database.db import async_session_maker
from app.database.models.chats import ChatsTable
from app.database.models.files import FilesTable
from app.database.models.message import MessagesTable
from app.schemas.chat_schema import InitChatReqSchema
from app.utils import get_id

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
)


class MessageType(TypedDict):
    file_id: str
    text: str


@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")


@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")


@sio.event
async def join_chat(sid, chat_id: str):
    await sio.enter_room(id, f"chat_{chat_id}")
    print(f"User {sid} joined the chat")


@sio.event
async def send_message(sid, data: MessageType):

    print(f"Message from {sid} - {data['text']}")

    db = async_session_maker()

    result = "Hello bro, how are you?"

    # result = await ask_service.ask_question(
    #     data=AskRequestSchema(query=data.text, file_id=data.file_id),
    #     db=db,
    # )

    await sio.emit(
        "receive_message",
        {
            "text": result,
            "file_id": data["file_id"],
        },
        to=sid,
    )


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

        return new_chat

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


chat_service = ChatService()
