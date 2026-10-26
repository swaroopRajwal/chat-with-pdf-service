from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.schemas.reply_schema import ReplyRequestSchema
from app.services.reply_service import reply_service

# /api/reply
router = APIRouter()

SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}


# Chats live in the client, so this only streams a reply for the messages it is given
@router.post("")
async def reply(data: ReplyRequestSchema, db: AsyncSession = Depends(get_db)):
    await reply_service.validate(data=data, db=db)

    return StreamingResponse(
        reply_service.stream_reply(data=data, db=db),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )
