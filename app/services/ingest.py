import pymupdf
import pymupdf4llm
from fastapi import HTTPException, UploadFile, status
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import EmbeddingsTable, FilesTable
from app.schemas.api_response import ResponseSchema
from app.settings import settings
from app.utils import get_id


class PDFResultType(BaseModel):
    file_name: str
    pdf_content: list[dict]


class CreateLangDocsType(BaseModel):
    no_of_docs: int
    docs: list[Document]


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

    def _create_langchain_documents(
        self,
        pdfs: PDFResultType.pdf_content,
        file_name: PDFResultType.file_name,
        file_id: str,
    ) -> CreateLangDocsType:

        lang_docs: list[Document] = []

        for page in pdfs:
            page["metadata"]["file_name"] = file_name
            page["metadata"]["file_id"] = file_id

            doc = Document(page_content=page["text"], metadata=page["metadata"])

            lang_docs.append(doc)

        return CreateLangDocsType(
            no_of_docs=len(lang_docs),
            docs=lang_docs,
        )

    def _create_chunks(self, docs: list[Document]):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

        chunks = text_splitter.split_documents(documents=docs)

        return chunks

    def _create_embeddings(self, docs: list[Document]):
        texts = [doc.page_content for doc in docs]

        embeddings_model = HuggingFaceEmbeddings(model_name=settings.embedding_model)

        vectors = embeddings_model.embed_documents(texts=texts)

        return vectors

    async def _insert_embeddings(
        self, chunks: list[Document], embeddings: list[list[float]], db: AsyncSession
    ):
        for chunk, vector in zip(chunks, embeddings):
            id = get_id()
            new_record = EmbeddingsTable(
                id=id,
                embeddings=vector,
                content=chunk.page_content,
                meta=chunk.metadata,
                file_id=chunk.metadata["file_id"],
            )
            db.add(new_record)

        await db.commit()

    async def upload_pdf(
        self,
        file: UploadFile,
        db: AsyncSession,
    ):
        processed_pdf = await self._get_readable_pdf(file)

        file_id = get_id()

        langchain_documents = self._create_langchain_documents(
            pdfs=processed_pdf.pdf_content,
            file_name=processed_pdf.file_name,
            file_id=file_id,
        )

        chunks = self._create_chunks(docs=langchain_documents.docs)

        embeddings = self._create_embeddings(docs=chunks)

        await self._insert_embeddings(chunks=chunks, embeddings=embeddings, db=db)

        file_entry = FilesTable(
            id=file_id,
            file_name=processed_pdf.file_name,
            pages_count=len(processed_pdf.pdf_content),
        )

        db.add(file_entry)
        await db.commit()

        return ResponseSchema(
            status=True,
            data=file_entry,
        )


ingest_service = IngestService()
