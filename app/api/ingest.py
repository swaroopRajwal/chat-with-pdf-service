from fastapi import APIRouter, UploadFile

from app.services.ingest import IngestService

# /api/ingest
router = APIRouter()


@router.post("")
async def upload_pdf(
    file: UploadFile,
):
    return await IngestService.upload_pdf(file=file)
