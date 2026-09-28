"""Operações de persistência do catálogo de filmes.

Todas as funções devolvem DTOs prontos para a camada HTTP. Relacionamentos são
carregados com ``selectinload`` porque lazy loading não é permitido em sessões
assíncronas.
"""

from collections.abc import Sequence
from typing import Any
from uuid import uuid4

from sqlalchemy import ColumnElement, Select, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import InvalidReferenceError, NotFoundError
from app.movies.crud.cache import catalog_cache, catalog_key, invalidate_catalog
from app.movies.crud.review import get_rating_summaries, get_rating_summary
from app.movies.models import (
    DimGenre,
    DimMovie,
    DimPerson,
    FactMoviePerformance,
    MovieReview,
)
from app.movies.schemas import (
    GenreRead,
    MovieCreate,
    MovieDetail,
    MovieFilters,
    MovieSort,
    MovieSummary,
    MovieUpdate,
    Page,
    PageParams,
    RatingSummary,
)

DIRECTOR = "Diretor"
_RELATION_FIELDS = {"genero_ids", "diretores"}


# --------------------------------------------------------------------------- #
# Mapeamento ORM -> DTO
# --------------------------------------------------------------------------- #
def _summary_payload(movie: DimMovie, rating: RatingSummary) -> dict[str, Any]:
    return {
        "id": movie.sk_movie_id,
        "titulo": movie.titulo,
        "ano_lancamento": movie.ano_lancamento,
        "url_poster": movie.url_poster,
        "generos": movie.genres,
        "avaliacao": rating,
    }


def _to_detail(movie: DimMovie, rating: RatingSummary) -> MovieDetail:
    people_by_role: dict[str, list[DimPerson]] = {"Ator": [], "Diretor": [], "Roteirista": []}
    for person in sorted(movie.people, key=lambda p: p.nome_pessoa):
        people_by_role[person.tipo_pessoa].append(person)

    return MovieDetail.model_validate(
        {
            **_summary_payload(movie, rating),
            "data_lancamento": movie.data_lancamento,
            "duracao_minutos": movie.duracao_minutos,
            "status_filme": movie.status_filme,
            "sinopse": movie.sinopse,
            "url_backdrop": movie.url_backdrop,
            "diretores": people_by_role["Diretor"],
            "roteiristas": people_by_role["Roteirista"],
            "elenco": people_by_role["Ator"],
            "produtoras": movie.companies,
            "desempenho": movie.performance,
        }
    )


# --------------------------------------------------------------------------- #
# Consultas
# --------------------------------------------------------------------------- #
def _escape_like(term: str) -> str:
    return term.replace("\\", "\\\\").replace("%", "\%").replace("_", "\_")


def _filter_conditions(filters: MovieFilters) -> list[ColumnElement[bool]]:
    conditions: list[ColumnElement[bool]] = []
    if filters.q:
        conditions.append(DimMovie.titulo.ilike(f"%{_escape_like(filters.q)}%", escape="\\"))
    if filters.genero_id:
        conditions.append(DimMovie.genres.any(DimGenre.sk_genre_id == filters.genero_id))
    if filters.ano is not None:
        conditions.append(DimMovie.ano_lancamento == filters.ano)
    return conditions


def _catalog_query(filters: MovieFilters) -> Select[tuple[DimMovie]]:
    """Filmes filtrados e ordenados, com desempate determinístico por PK.

    Os JOINs são INNER de propósito, para que o SQLite percorra os índices de
    ordenação em vez de ordenar a tabela inteira.
    """

    stmt = select(DimMovie).where(*_filter_conditions(filters))
    match filters.ordenar:
        case MovieSort.POPULARES:
            # Todo filme possui linha no fato (carga + create_movie). No SQLite,
            # NULL já fica por último em ordenação DESC.
            return stmt.join(FactMoviePerformance).order_by(
                FactMoviePerformance.popularidade.desc(), FactMoviePerformance.sk_movie_id.desc()
            )
        case MovieSort.RECENTES:
            return stmt.order_by(DimMovie.data_lancamento.desc(), DimMovie.sk_movie_id)
        case MovieSort.TITULO:
            return stmt.order_by(DimMovie.titulo, DimMovie.sk_movie_id)
        case MovieSort.MELHOR_AVALIADOS:
            stats = (
                select(
                    MovieReview.sk_movie_id,
                    func.avg(MovieReview.nota).label("media"),
                    func.count().label("total"),
                )
                .group_by(MovieReview.sk_movie_id)
                .subquery("review_stats")
            )
            # Ranking por nota considera apenas filmes com ao menos uma avaliação.
            return stmt.join(stats, stats.c.sk_movie_id == DimMovie.sk_movie_id).order_by(
                stats.c.media.desc(), stats.c.total.desc(), DimMovie.sk_movie_id
            )


async def list_movies(
    session: AsyncSession, filters: MovieFilters, params: PageParams
) -> Page[MovieSummary]:
    """Catálogo paginado com busca por título, filtros e média de avaliações.

    Resultados ficam em cache por alguns segundos (``catalog_cache``): a mesma
    página é pedida muitas vezes (paginação, voltar do navegador) e o catálogo
    só muda quando há escrita, que invalida o cache.
    """

    key = catalog_key(filters, params)
    if (cached := catalog_cache.get(key)) is not None:
        return cached

    stmt = _catalog_query(filters)
    total = await session.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    movies = list(
        await session.scalars(
            stmt.options(selectinload(DimMovie.genres)).offset(params.offset).limit(params.size)
        )
    )

    # Médias calculadas só para a página atual: custo O(tamanho da página).
    ratings = await get_rating_summaries(session, [m.sk_movie_id for m in movies])
    items = [
        MovieSummary.model_validate(_summary_payload(movie, ratings[movie.sk_movie_id]))
        for movie in movies
    ]
    page = Page[MovieSummary].build(items, total or 0, params)
    catalog_cache.set(key, page)
    return page


async def _load_movie(session: AsyncSession, movie_id: str) -> DimMovie:
    movie = await session.scalar(
        select(DimMovie)
        .where(DimMovie.sk_movie_id == movie_id)
        .options(
            selectinload(DimMovie.genres),
            selectinload(DimMovie.companies),
            selectinload(DimMovie.people),
            selectinload(DimMovie.performance),
        )
        .execution_options(populate_existing=True)
    )
    if movie is None:
        raise NotFoundError(f"Filme {movie_id} não encontrado")
    return movie


async def get_movie(session: AsyncSession, movie_id: str) -> MovieDetail:
    movie = await _load_movie(session, movie_id)
    return _to_detail(movie, await get_rating_summary(session, movie_id))


async def list_genres(session: AsyncSession) -> list[GenreRead]:
    genres = await session.scalars(select(DimGenre).order_by(DimGenre.nome_genero))
    return [GenreRead.model_validate(g) for g in genres]


# --------------------------------------------------------------------------- #
# Escrita
# --------------------------------------------------------------------------- #
async def _resolve_genres(session: AsyncSession, genre_ids: Sequence[str]) -> list[DimGenre]:
    unique_ids = set(genre_ids)
    if not unique_ids:
        return []
    genres = list(
        await session.scalars(select(DimGenre).where(DimGenre.sk_genre_id.in_(unique_ids)))
    )
    missing = unique_ids - {g.sk_genre_id for g in genres}
    if missing:
        raise InvalidReferenceError(f"Gêneros inexistentes: {', '.join(sorted(missing))}")
    return genres


async def _resolve_directors(session: AsyncSession, names: Sequence[str]) -> list[DimPerson]:
    """Obtém diretores por nome, criando os que ainda não existem (get-or-create)."""

    unique_names = list(dict.fromkeys(names))  # remove duplicatas preservando a ordem
    if not unique_names:
        return []
    existing = {
        p.nome_pessoa: p
        for p in await session.scalars(
            select(DimPerson).where(
                DimPerson.tipo_pessoa == DIRECTOR, DimPerson.nome_pessoa.in_(unique_names)
            )
        )
    }
    return [
        existing.get(name) or DimPerson(nome_pessoa=name, tipo_pessoa=DIRECTOR)
        for name in unique_names
    ]


def _derive_release_year(movie: DimMovie) -> None:
    if movie.data_lancamento is not None:
        movie.ano_lancamento = movie.data_lancamento.year


async def create_movie(session: AsyncSession, data: MovieCreate) -> MovieDetail:
    movie = DimMovie(
        # id_filme identifica o filme na origem (TMDB); cadastros locais recebem um id próprio.
        id_filme=f"cinebox-{uuid4().hex}",
        # Invariante do esquema estrela: todo filme tem uma linha no fato.
        performance=FactMoviePerformance(),
        **data.model_dump(exclude=_RELATION_FIELDS),
    )
    _derive_release_year(movie)
    movie.genres = await _resolve_genres(session, data.genero_ids)
    movie.people = await _resolve_directors(session, data.diretores)

    session.add(movie)
    await session.commit()
    invalidate_catalog()
    return await get_movie(session, movie.sk_movie_id)


async def update_movie(session: AsyncSession, movie_id: str, data: MovieUpdate) -> MovieDetail:
    movie = await _load_movie(session, movie_id)

    for field, value in data.model_dump(exclude_unset=True, exclude=_RELATION_FIELDS).items():
        setattr(movie, field, value)
    if "data_lancamento" in data.model_fields_set:
        _derive_release_year(movie)

    if data.genero_ids is not None:
        movie.genres = await _resolve_genres(session, data.genero_ids)
    if data.diretores is not None:
        others = [p for p in movie.people if p.tipo_pessoa != DIRECTOR]
        movie.people = others + await _resolve_directors(session, data.diretores)

    await session.commit()
    invalidate_catalog()
    return await get_movie(session, movie_id)


async def delete_movie(session: AsyncSession, movie_id: str) -> None:
    """Remove o filme; bridges, fato e avaliações caem via ``ON DELETE CASCADE``.

    DELETE em nível de Core evita carregar todas as coleções só para apagá-las.
    """

    result = await session.execute(delete(DimMovie).where(DimMovie.sk_movie_id == movie_id))
    if result.rowcount == 0:
        await session.rollback()
        raise NotFoundError(f"Filme {movie_id} não encontrado")
    await session.commit()
    invalidate_catalog()
