import pymupdf
import pymupdf4llm
from fastapi import HTTPException, UploadFile, status
from langchain_core.documents import Document
from pydantic import BaseModel

from app.utils import get_id


class PDFResultType(BaseModel):
    file_name: str
    pdf_content: list[dict]


class IngestService:
    async def _get_readable_pdf(self, file: UploadFile) -> PDFResultType:

        file_name = file.filename

        if not file_name.endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please upload a PDF file",
            )

        file_bytes = await file.read()

        doc = pymupdf.open(
            stream=file_bytes,
            filetype="pdf",
        )

        pdf_texts = pymupdf4llm.to_text(doc, page_chunks=True)

        return PDFResultType(
            file_name=file_name,
            pdf_content=pdf_texts,
        )

    async def upload_pdf(self, file: UploadFile):
        processed_pdf = await self._get_readable_pdf(file)

        file_id = get_id()

        lang_docs: list[Document] = []

        for page in processed_pdf.pdf_content:
            page["metadata"]["file_name"] = processed_pdf.file_name
            page["metadata"]["file_id"] = file_id

            doc = Document(page_content=page["text"], metadata=page["metadata"])

            lang_docs.append(doc)

        return {
            "status": True,
            "no_of_docs": len(lang_docs),
            "lang_docs": lang_docs,
        }


ingest_service = IngestService()
