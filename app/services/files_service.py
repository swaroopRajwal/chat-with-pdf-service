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


files_service = FilesService()
