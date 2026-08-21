from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ResponseSchema[T](BaseModel):
    status: bool
    data: T


class PaginatedResponseSchema[T](BaseModel):
    status: bool
    data: list[T]
    page: int
    limit: int
    count: int
