import fastapi_swagger_dark as docs_dark_theme
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import ask_api, chat_api, files_api, ingest_api
from app.api.chat_api import socket_app
from app.database.db import get_db
from app.database.models.health import HealthTable

app = FastAPI(docs_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Swagger UI dark theme
docs_dark_theme_router = APIRouter()
docs_dark_theme.install(docs_dark_theme_router)
app.include_router(docs_dark_theme_router)

app.include_router(ingest_api.router, prefix="/api/ingest", tags=["Ingest"])
app.include_router(ask_api.router, prefix="/api/ask", tags=["Ask"])
app.include_router(files_api.router, prefix="/api/files", tags=["Files"])
app.include_router(chat_api.router, prefix="/api/chat/init", tags=["Chat"])
app.mount("/chat", socket_app)


@app.get("/")
def home():
    return {
        "status": True,
        "message": "Check service health on /health and docs on /docs",
    }


@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(HealthTable))
    result = result.scalars().first()

    if result:
        return {"status": True, "message": result.message}

    return {
        "status": True,
        "message": "Database connection established",
    }


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    # This intercepts EVERY HTTPException and reformats it
    return JSONResponse(
        status_code=exc.status_code, content={"status": False, "message": exc.detail}
    )
