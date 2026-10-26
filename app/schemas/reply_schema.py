from typing import Literal

from pydantic import BaseModel, Field


class ReplyMessageSchema(BaseModel):
    role: Literal["USER", "AI"]
    content: str = Field(min_length=1)


class ReplyRequestSchema(BaseModel):
    file_id: str = Field(min_length=1)
    # The whole conversation so far; the last message must be from the user
    messages: list[ReplyMessageSchema] = Field(min_length=1)
