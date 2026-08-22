from pydantic import BaseModel, Field


class AskRequestSchema(BaseModel):
    query: str = Field(min_length=1)
    file_id: str = Field(min_length=1)


class AskResponseSchema(BaseModel):
    query: str = Field(min_length=1)
    answer: str = Field(min_length=1)
