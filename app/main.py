from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.database.models.health import HealthTable

app = FastAPI()


@app.get("/")
def home():
    return {
        "status": True,
        "message": "Check service health on /health and docs on /docs",
    }


@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(HealthTable))
    message = result.scalars().first().message

    return {
        "status": True,
        "message": message,
    }


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    # This intercepts EVERY HTTPException and reformats it
    return JSONResponse(
        status_code=exc.status_code, content={"status": False, "message": exc.detail}
    )
