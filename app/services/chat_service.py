from typing import TypedDict

import socketio

from app.database.db import async_session_maker

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
