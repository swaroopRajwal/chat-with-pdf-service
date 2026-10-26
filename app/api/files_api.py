from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.schemas.api_response_schema import PaginatedResponseSchema, ResponseSchema
from app.schemas.files_schema import FilesBaseSchema
from app.services.files_service import files_service

# /api/files
router = APIRouter()


@router.get("", response_model=PaginatedResponseSchema[FilesBaseSchema])
async def get_all_files(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    sort_by: Literal["file_name", "created_at", "pages_count"] = "created_at",
    order: Literal["asc", "desc"] = "desc",
    db: AsyncSession = Depends(get_db),
):
    files, count = await files_service.get_all_files(
        db=db, page=page, limit=limit, sort_by=sort_by, order=order
    )

    return PaginatedResponseSchema(
        status=True,
        data=files,
        page=page,
        limit=limit,
        count=count,
    )


@router.get("/{file_id}", response_model=ResponseSchema[FilesBaseSchema])
async def get_single_file(file_id: str, db: AsyncSession = Depends(get_db)):
    result = await files_service.get_single_file(file_id=file_id, db=db)

    return ResponseSchema(
        status=True,
        data=result,
    )
