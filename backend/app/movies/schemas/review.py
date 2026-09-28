"""DTOs de avaliações. Notas na escala de 0 a 10, a mesma do banco (``movie_reviews``)."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

Score = Annotated[float, Field(ge=0, le=10)]
"""Nota de 0 a 10, conforme definido nas models (orientação oficial da atividade)."""


class ReviewCreate(BaseModel):
    nome: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
    nota: Score
    comentario: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)
    ]


class ReviewRead(BaseModel):
    id: str
    nome: str
    nota: Score
    comentario: str
    created_at: datetime


class RatingSummary(BaseModel):
    """Média geral (0 a 10) e quantidade de avaliações de um filme."""

    nota_media: Score | None
    total_avaliacoes: int
