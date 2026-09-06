import socketio
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.schemas.api_response_schema import ResponseSchema
from app.schemas.chat_schema import ChatsBaseSchema, InitChatReqSchema
from app.services.chat_service import chat_service, sio

socket_app = socketio.ASGIApp(socketio_server=sio, socketio_path="/chat/socket.io")

# This is used to initiate a new chat and create base messages
# /api/chat/init
router = APIRouter()


@router.post("", response_model=ResponseSchema[ChatsBaseSchema])
async def init_chat(data: InitChatReqSchema, db: AsyncSession = Depends(get_db)):
    result = await chat_service.init_chat(data=data, db=db)

    return ResponseSchema(
        status=True,
        data=result,
    )
