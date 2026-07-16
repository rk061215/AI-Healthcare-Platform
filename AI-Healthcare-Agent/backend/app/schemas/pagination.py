from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = 1
    per_page: int = 20


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    per_page: int
    total_pages: int

    @classmethod
    def create(cls, items: list[T], total: int, page: int, per_page: int) -> "PaginatedResponse[T]":
        return cls(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=max(1, (total + per_page - 1) // per_page),
        )
