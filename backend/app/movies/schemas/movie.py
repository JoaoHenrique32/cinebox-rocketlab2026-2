"""DTOs de filmes."""

from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import AliasChoices, BaseModel, Field, StringConstraints, model_validator

from app.movies.models import PersonType
from app.movies.schemas.common import ORMModel, PageParams
from app.movies.schemas.review import RatingSummary

MovieStatus = Literal["Lançado", "Em Produção", "Pós-Produção", "Planejado"]

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
PersonName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
HttpUrlStr = Annotated[str, StringConstraints(max_length=2048, pattern=r"^https?://\S+$")]
Year = Annotated[int, Field(ge=1870, le=2100)]
Minutes = Annotated[int, Field(ge=1, le=1000)]
Synopsis = Annotated[str, StringConstraints(strip_whitespace=True, max_length=4000)]


class MovieSort(StrEnum):
    POPULARES = "populares"
    RECENTES = "recentes"
    TITULO = "titulo"
    MELHOR_AVALIADOS = "melhor_avaliados"


class MovieFilters(BaseModel):
    """Critérios de busca do catálogo."""

    q: Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)] | None = None
    genero_id: str | None = None
    ano: Year | None = None
    ordenar: MovieSort = MovieSort.POPULARES


class MovieListQuery(MovieFilters, PageParams):
    """Query string do catálogo (o FastAPI aceita um único modelo por requisição)."""


# --------------------------------------------------------------------------- #
# Leitura
# --------------------------------------------------------------------------- #
class GenreRead(ORMModel):
    id: str = Field(validation_alias=AliasChoices("sk_genre_id", "id"))
    nome: str = Field(validation_alias=AliasChoices("nome_genero", "nome"))


class CompanyRead(ORMModel):
    id: str = Field(validation_alias=AliasChoices("sk_company_id", "id"))
    nome: str = Field(validation_alias=AliasChoices("nome_produtora", "nome"))


class PersonRead(ORMModel):
    id: str = Field(validation_alias=AliasChoices("sk_person_id", "id"))
    nome: str = Field(validation_alias=AliasChoices("nome_pessoa", "nome"))
    tipo: PersonType = Field(validation_alias=AliasChoices("tipo_pessoa", "tipo"))


class PerformanceRead(ORMModel):
    orcamento_usd: Decimal | None
    receita_usd: Decimal | None
    lucro_usd: Decimal
    popularidade: float | None
    nota_tmdb: float | None
    qtd_tmdb: int | None
    nota_imdb: float | None
    qtd_imdb: int | None


class MovieSummary(ORMModel):
    """Item do catálogo (card)."""

    id: str = Field(validation_alias=AliasChoices("sk_movie_id", "id"))
    titulo: str
    ano_lancamento: int | None
    url_poster: str | None
    generos: list[GenreRead] = Field(validation_alias=AliasChoices("genres", "generos"))
    avaliacao: RatingSummary


class MovieDetail(MovieSummary):
    """Informações completas de um filme."""

    data_lancamento: date | None
    duracao_minutos: int | None
    status_filme: str | None
    sinopse: str | None
    url_backdrop: str | None
    diretores: list[PersonRead]
    roteiristas: list[PersonRead]
    elenco: list[PersonRead]
    produtoras: list[CompanyRead] = Field(validation_alias=AliasChoices("companies", "produtoras"))
    desempenho: PerformanceRead | None = Field(
        validation_alias=AliasChoices("performance", "desempenho")
    )


# --------------------------------------------------------------------------- #
# Escrita
# --------------------------------------------------------------------------- #
class _MovieWriteFields(BaseModel):
    """Campos editáveis compartilhados por criação e atualização."""

    data_lancamento: date | None = None
    ano_lancamento: Year | None = None
    duracao_minutos: Minutes | None = None
    status_filme: MovieStatus | None = None
    sinopse: Synopsis | None = None
    url_poster: HttpUrlStr | None = None
    url_backdrop: HttpUrlStr | None = None

    @model_validator(mode="after")
    def _release_date_matches_year(self) -> Self:
        if (
            self.data_lancamento is not None
            and self.ano_lancamento is not None
            and self.data_lancamento.year != self.ano_lancamento
        ):
            raise ValueError("ano_lancamento difere do ano de data_lancamento")
        return self


class MovieCreate(_MovieWriteFields):
    titulo: Title
    genero_ids: list[str] = Field(default_factory=list, max_length=19)
    diretores: list[PersonName] = Field(default_factory=list, max_length=20)


class MovieUpdate(_MovieWriteFields):
    """Atualização parcial (PATCH): apenas os campos enviados são alterados.

    Listas (``genero_ids``/``diretores``), quando enviadas, substituem as atuais.
    """

    titulo: Title | None = None
    genero_ids: list[str] | None = Field(None, max_length=19)
    diretores: list[PersonName] | None = Field(None, max_length=20)

    @model_validator(mode="after")
    def _reject_null_on_required(self) -> Self:
        for field in ("titulo", "genero_ids", "diretores"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} não pode ser nulo")
        return self
