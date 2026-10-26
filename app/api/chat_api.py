import socketio
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from litellm import acompletion
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import MESSAGES_ROLES
from app.database.db import get_db
from app.database.models.chats import ChatsTable
from app.database.models.message import MessagesTable
from app.schemas.api_response_schema import ResponseSchema
from app.schemas.chat_schema import (
    ChatAskRequestSchema,
    ChatDetailSchema,
    ChatsBaseSchema,
    ChatsWithFileSchema,
    InitChatReqSchema,
    MessagesBaseSchema,
)
from app.services.chat_service import chat_service, sio
from app.settings import settings
from app.utils import get_id

socket_app = socketio.ASGIApp(socketio_server=sio, socketio_path="/chat/socket.io")

# This is used to initiate a new chat and create base messages
# /api/chats
router = APIRouter()


@router.post("/init", response_model=ResponseSchema[ChatsBaseSchema])
async def init_chat(data: InitChatReqSchema, db: AsyncSession = Depends(get_db)):
    result = await chat_service.init_chat(data=data, db=db)

    return ResponseSchema(
        status=True,
        data=result,
    )


@router.get("", response_model=ResponseSchema[list[ChatsWithFileSchema]])
async def get_all_chats(db: AsyncSession = Depends(get_db)):
    chats = await chat_service.get_all_chats(db=db)

    return ResponseSchema(
        status=True,
        data=chats,
    )


@router.get("/{chat_id}", response_model=ResponseSchema[ChatDetailSchema])
async def get_chat(chat_id: str, db: AsyncSession = Depends(get_db)):
    chat = await chat_service.get_chat_by_id(chat_id=chat_id, db=db)

    return ResponseSchema(
        status=True,
        data=chat,
    )


async def stream_response(
    messages: list[MessagesBaseSchema], db: AsyncSession, chat: ChatsTable
):
    full_reply = ""
    try:
        response = await acompletion(
            model=settings.llm_model,
            api_key=settings.llm_api_key,
            api_base=settings.llm_api_base,
            api_version=None,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            messages=messages,
            stream=True,
        )

        async for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                full_reply += content
                escaped = content.replace("\\", "\\\\").replace("\n", "\\n")
                yield f"data: {escaped}\n\n"
    finally:
        if full_reply:
            ai_response = MessagesTable(
                id=get_id(),
                chat_id=chat.id,
                content=full_reply,
                role=MESSAGES_ROLES["ai"],
                order=len(messages) + 1,
                chat=chat,
            )
            db.add(ai_response)

            await db.commit()

            yield "data: [DONE]\n\n"


@router.post("/{chat_id}/ask", response_model=ResponseSchema[MessagesBaseSchema])
async def ask_query(
    chat_id: str, data: ChatAskRequestSchema, db: AsyncSession = Depends(get_db)
):

    chat = await db.execute(select(ChatsTable).where(ChatsTable.id == chat_id))

    chat = chat.scalars().first()

    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )

    chat_history = []
    for msg in data.all_messages:
        role = ""
        content = msg.content

        if msg.role == MESSAGES_ROLES["user"]:
            role = "user"
        else:
            role = "assistant"
        chat_history.append({"role": role, "content": content})

    new_message = MessagesTable(
        id=get_id(),
        chat_id=chat.id,
        content=data.message.content,
        role=MESSAGES_ROLES["user"],
        order=data.message.order,
        chat=chat,
    )
    db.add(new_message)
    await db.commit()

    chat_history.append({"role": "user", "content": new_message.content})

    return StreamingResponse(
        stream_response(
            messages=chat_history,
            db=db,
            chat=chat,
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
