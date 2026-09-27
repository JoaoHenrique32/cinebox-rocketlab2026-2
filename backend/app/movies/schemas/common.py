"""DTOs genéricos compartilhados pelo domínio."""

from math import ceil
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

MAX_PAGE_SIZE = 100

T = TypeVar("T")


class PageParams(BaseModel):
    """Parâmetros de paginação por offset."""

    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=MAX_PAGE_SIZE)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


class Page(BaseModel, Generic[T]):
    """Envelope de resposta paginada."""

    items: list[T]
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def build(cls, items: list[T], total: int, params: PageParams) -> "Page[T]":
        return cls(
            items=items,
            total=total,
            page=params.page,
            size=params.size,
            pages=ceil(total / params.size) if total else 0,
        )


class ORMModel(BaseModel):
    """Base para DTOs lidos diretamente de objetos ORM."""

    model_config = ConfigDict(from_attributes=True)
