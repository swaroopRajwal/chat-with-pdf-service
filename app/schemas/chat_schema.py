from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.files_schema import FilesBaseSchema


class InitChatReqSchema(BaseModel):
    query: str = Field(min_length=1)
    file_id: str = Field(min_length=1)


class MessagesBaseSchema(BaseModel):
    id: str = Field(min_length=1)
    chat_id: str = Field(min_length=1)
    content: str = Field(min_length=1)
    role: str = Field(min_length=1)
    order: int

    model_config = {"from_attributes": True}


class ChatsBaseSchema(BaseModel):
    id: str = Field(min_length=1)
    client_id: str = Field(min_length=1)
    file_id: str = Field(min_length=1)
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatsWithFileSchema(ChatsBaseSchema):
    file: FilesBaseSchema

    model_config = {"from_attributes": True}


class ChatDetailSchema(ChatsWithFileSchema):
    messages: list[MessagesBaseSchema]

    model_config = {"from_attributes": True}
