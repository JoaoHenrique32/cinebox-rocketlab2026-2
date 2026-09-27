"""DTOs de avaliações. Toda nota exposta aqui está na escala de 1 a 5 estrelas."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

Stars = Annotated[float, Field(ge=1, le=5, multiple_of=0.5)]
"""Nota de entrada: 1 a 5 estrelas, com meia estrela (como no Letterboxd)."""

StarsAverage = Annotated[float, Field(ge=0, le=5)]
"""Nota de saída: médias e notas históricas do CSV podem ficar abaixo de 1."""


class ReviewCreate(BaseModel):
    nome: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
    estrelas: Stars
    comentario: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)
    ]


class ReviewRead(BaseModel):
    id: str
    nome: str
    estrelas: StarsAverage
    comentario: str
    created_at: datetime


class RatingSummary(BaseModel):
    """Média geral e quantidade de avaliações de um filme."""

    media_estrelas: StarsAverage | None
    total_avaliacoes: int
