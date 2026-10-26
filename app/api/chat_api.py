from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import MESSAGES_ROLES
from app.database.db import get_db
from app.schemas.api_response_schema import ResponseSchema
from app.schemas.chat_schema import (
    ChatAskRequestSchema,
    ChatDetailSchema,
    ChatsWithFileSchema,
    InitChatReqSchema,
)
from app.services.chat_service import chat_service

# /api/chats
router = APIRouter()

SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}


# Creates the chat and its first message, then streams the reply to it
@router.post("/init")
async def init_chat(data: InitChatReqSchema, db: AsyncSession = Depends(get_db)):
    chat, first_message = await chat_service.init_chat(data=data, db=db)

    return StreamingResponse(
        chat_service.stream_reply(
            chat=chat, messages=[first_message], db=db, announce_chat=True
        ),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
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


@router.post("/{chat_id}/ask")
async def ask_query(
    chat_id: str, data: ChatAskRequestSchema, db: AsyncSession = Depends(get_db)
):
    chat = await chat_service.get_chat(chat_id=chat_id, db=db)
    messages = await chat_service.get_messages(chat_id=chat.id, db=db)

    if data.content:
        new_message = await chat_service.add_user_message(
            chat=chat, messages=messages, content=data.content, db=db
        )
        messages.append(new_message)
    elif not messages or messages[-1].role != MESSAGES_ROLES["user"]:
        # Retry only makes sense when the last user message has no reply
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="There is no unanswered message to retry",
        )

    return StreamingResponse(
        chat_service.stream_reply(chat=chat, messages=messages, db=db),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )
