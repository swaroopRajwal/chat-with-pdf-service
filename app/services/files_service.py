from fastapi import HTTPException, status
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import FilesTable


class FilesService:
    async def get_all_files(
        self,
        db: AsyncSession,
        page: int,
        limit: int,
        sort_by: Literal["file_name", "created_at", "pages_count"],
        order: Literal["asc", "desc"],
    ):
        column = getattr(FilesTable, sort_by)
        count = await db.scalar(select(func.count()).select_from(FilesTable)) or 0

        result = await db.execute(
            select(FilesTable)
            .order_by(column.asc() if order == "asc" else column.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )

        return result.scalars().all(), count

    async def get_single_file(self, file_id: str, db: AsyncSession):
        result = await db.execute(select(FilesTable).where(FilesTable.id == file_id))

        file = result.scalars().first()

        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
            )

        return file


files_service = FilesService()
