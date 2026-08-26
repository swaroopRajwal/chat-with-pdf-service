from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import FilesTable
from app.schemas.api_response_schema import ResponseSchema


class FilesService:
    async def get_all_files(self, db: AsyncSession):
        result = await db.execute(select(FilesTable))
        files = result.scalars().all()

        return ResponseSchema(
            status=True,
            data=files,
        )

    async def get_single_file(self, file_id: str, db: AsyncSession):
        result = await db.execute(select(FilesTable).where(FilesTable.id == file_id))

        file = result.scalars().first()

        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
            )

        return ResponseSchema(status=True, data=file)


files_service = FilesService()
