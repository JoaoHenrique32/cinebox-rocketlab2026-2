"""Exceções de domínio.

A camada ``crud/`` sinaliza falhas de regra de negócio com estas exceções; a
camada HTTP apenas as traduz para status codes, sem conhecer as regras.
"""


class DomainError(Exception):
    """Base para erros de regra de negócio."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    """O recurso solicitado não existe."""


class InvalidReferenceError(DomainError):
    """O payload referencia entidades inexistentes (ex.: gênero desconhecido)."""
