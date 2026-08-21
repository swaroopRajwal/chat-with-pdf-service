from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.schemas.api_response import ResponseSchema
from app.schemas.ingest import IngestBaseSchema
from app.services.ingest import ingest_service

# /api/ingest
router = APIRouter()


@router.post("", response_model=ResponseSchema[IngestBaseSchema])
async def upload_pdf(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
):
    return await ingest_service.upload_pdf(file=file, db=db)
