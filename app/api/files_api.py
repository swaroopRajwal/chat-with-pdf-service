from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.schemas.api_response_schema import ResponseSchema
from app.schemas.files_schema import FilesBaseSchema
from app.services.files_service import files_service

# /api/files
router = APIRouter()


@router.get("", response_model=ResponseSchema[list[FilesBaseSchema]])
async def get_all_files(db: AsyncSession = Depends(get_db)):
    return await files_service.get_all_files(db=db)
