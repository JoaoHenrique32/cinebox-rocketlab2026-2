"""Camada de acesso a dados do domínio de filmes.

Regras de negócio vivem aqui; a
camada HTTP apenas delega e traduz exceções de domínio em status codes.
"""

from app.movies.crud import movie, review

__all__ = ["movie", "review"]
