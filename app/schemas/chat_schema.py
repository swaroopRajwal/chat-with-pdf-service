from datetime import datetime

from pydantic import BaseModel, Field


class InitChatReqSchema(BaseModel):
    query: str = Field(min_length=1)
    file_id: str = Field(min_length=1)


class ChatsBaseSchema(BaseModel):
    id: str = Field(min_length=1)
    client_id: str = Field(min_length=1)
    file_id: str = Field(min_length=1)
    created_at: datetime
