"""Conversão entre a escala do banco (0-10) e a da API (estrelas, 0-5).

Único ponto do sistema que conhece as duas escalas.
"""

SCALE_FACTOR = 2


def to_stars(db_score: float) -> float:
    return round(db_score / SCALE_FACTOR, 2)


def to_db_score(stars: float) -> float:
    return stars * SCALE_FACTOR
