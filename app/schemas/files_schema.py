from datetime import datetime

from pydantic import BaseModel, Field


class FilesBaseSchema(BaseModel):
    id: str = Field(min_length=1)
    file_name: str = Field(min_length=1)
    pages_count: int
    created_at: datetime
