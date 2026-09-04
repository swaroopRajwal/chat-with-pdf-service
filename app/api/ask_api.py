from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.schemas.api_response_schema import ResponseSchema
from app.schemas.ask_schema import AskRequestSchema, AskResponseSchema
from app.services.ask_service import ask_service

# /api/ask
router = APIRouter()


@router.post("", response_model=ResponseSchema[AskResponseSchema])
async def ask_question(data: AskRequestSchema, db: AsyncSession = Depends(get_db)):
    result = await ask_service.ask_question(
        data=data,
        db=db,
    )
    return ResponseSchema(
        status=True,
        data={
            "query": data.query,
            "answer": result,
        },
    )
