"""Testes da camada CRUD do domínio de filmes."""

from datetime import date

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidReferenceError, NotFoundError
from app.movies.crud import movie as movie_crud
from app.movies.crud import review as review_crud
from app.movies.models import DimPerson, MovieReview, bridge_movie_genre
from app.movies.schemas import (
    MovieCreate,
    MovieFilters,
    MovieSort,
    MovieUpdate,
    PageParams,
    ReviewCreate,
)

# --------------------------------------------------------------------------- #
# Listagem, busca e média
# --------------------------------------------------------------------------- #


async def test_list_movies_defaults_to_popularity_with_star_average(
    session: AsyncSession, seeded: dict[str, str]
) -> None:
    page = await movie_crud.list_movies(session, MovieFilters(), PageParams())

    assert [m.titulo for m in page.items] == ["Mixtape", "Rings", "100% Wolf"]
    rings = page.items[1]
    assert rings.avaliacao.nota_media == 7.0  # (8 + 6) / 2
    assert rings.avaliacao.total_avaliacoes == 2
    assert page.items[2].avaliacao.nota_media is None
    assert [g.nome for g in rings.generos] == ["Horror"]


async def test_list_movies_paginates(session: AsyncSession, seeded: dict[str, str]) -> None:
    page = await movie_crud.list_movies(
        session, MovieFilters(ordenar=MovieSort.TITULO), PageParams(page=2, size=2)
    )

    assert (page.total, page.pages, page.page) == (3, 2, 2)
    assert [m.titulo for m in page.items] == ["Rings"]


async def test_search_is_case_insensitive_and_escapes_wildcards(
    session: AsyncSession, seeded: dict[str, str]
) -> None:
    by_title = await movie_crud.list_movies(session, MovieFilters(q="rIN"), PageParams())
    literal_percent = await movie_crud.list_movies(session, MovieFilters(q="%"), PageParams())

    assert [m.titulo for m in by_title.items] == ["Rings"]
    assert [m.titulo for m in literal_percent.items] == ["100% Wolf"]


async def test_filter_by_genre_and_best_rated_sort(
    session: AsyncSession, seeded: dict[str, str]
) -> None:
    dramas = await movie_crud.list_movies(
        session,
        MovieFilters(genero_id="g-drama", ordenar=MovieSort.MELHOR_AVALIADOS),
        PageParams(),
    )

    # Ranking por nota ignora filmes sem avaliação ("100% Wolf").
    assert dramas.total == 1
    assert [m.titulo for m in dramas.items] == ["Mixtape"]


# --------------------------------------------------------------------------- #
# Detalhe e escrita de filmes
# --------------------------------------------------------------------------- #


async def test_get_movie_groups_people_by_role(
    session: AsyncSession, seeded: dict[str, str]
) -> None:
    detail = await movie_crud.get_movie(session, seeded["rings"])

    assert [p.nome for p in detail.diretores] == ["Ana Diretora"]
    assert [p.nome for p in detail.elenco] == ["Beto Ator"]
    assert detail.desempenho is not None and detail.desempenho.popularidade == 10.0


async def test_get_unknown_movie_raises_not_found(session: AsyncSession) -> None:
    with pytest.raises(NotFoundError):
        await movie_crud.get_movie(session, "nope")


async def test_create_movie_links_genres_reuses_and_creates_directors(
    session: AsyncSession, seeded: dict[str, str]
) -> None:
    created = await movie_crud.create_movie(
        session,
        MovieCreate(
            titulo="  Novo Filme  ",
            data_lancamento=date(2024, 5, 1),
            genero_ids=["g-drama", "g-horror"],
            diretores=["Ana Diretora", "Caio Novo"],
        ),
    )

    assert created.titulo == "Novo Filme"
    assert created.ano_lancamento == 2024  # derivado da data
    assert {g.nome for g in created.generos} == {"Drama", "Horror"}
    assert [d.nome for d in created.diretores] == ["Ana Diretora", "Caio Novo"]
    assert created.desempenho is not None  # linha no fato criada junto
    directors = await session.scalar(
        select(func.count()).select_from(DimPerson).where(DimPerson.tipo_pessoa == "Diretor")
    )
    assert directors == 2  # "Ana Diretora" reaproveitada, não duplicada


async def test_create_movie_with_unknown_genre_is_rejected(
    session: AsyncSession, seeded: dict[str, str]
) -> None:
    with pytest.raises(InvalidReferenceError):
        await movie_crud.create_movie(session, MovieCreate(titulo="X", genero_ids=["g-ghost"]))


async def test_update_movie_is_partial_and_keeps_non_director_people(
    session: AsyncSession, seeded: dict[str, str]
) -> None:
    updated = await movie_crud.update_movie(
        session,
        seeded["rings"],
        MovieUpdate(sinopse="Nova sinopse", genero_ids=["g-drama"], diretores=["Outra Pessoa"]),
    )

    assert updated.titulo == "Rings"
    assert updated.sinopse == "Nova sinopse"
    assert [g.nome for g in updated.generos] == ["Drama"]
    assert [d.nome for d in updated.diretores] == ["Outra Pessoa"]
    assert [a.nome for a in updated.elenco] == ["Beto Ator"]


def test_update_schema_rejects_null_title() -> None:
    with pytest.raises(ValidationError):
        MovieUpdate(titulo=None)


async def test_delete_movie_cascades(session: AsyncSession, seeded: dict[str, str]) -> None:
    await movie_crud.delete_movie(session, seeded["rings"])

    reviews = await session.scalar(select(func.count()).select_from(MovieReview))
    bridges = await session.scalar(select(func.count()).select_from(bridge_movie_genre))
    assert reviews == 1  # só a avaliação de Mixtape
    assert bridges == 2  # Mixtape e 100% Wolf
    with pytest.raises(NotFoundError):
        await movie_crud.delete_movie(session, seeded["rings"])


# --------------------------------------------------------------------------- #
# Avaliações e escala de notas
# --------------------------------------------------------------------------- #


async def test_create_review_keeps_0_to_10_scale(
    session: AsyncSession, seeded: dict[str, str]
) -> None:
    review = await review_crud.create_review(
        session,
        seeded["percent"],
        ReviewCreate(nome="Admin", nota=8.5, comentario="Ótimo"),
    )

    stored = await session.scalar(select(MovieReview.nota).where(MovieReview.nome == "Admin"))
    assert stored == 8.5  # gravada sem conversão
    assert review.nota == 8.5
    summary = await review_crud.get_rating_summary(session, seeded["percent"])
    assert (summary.nota_media, summary.total_avaliacoes) == (8.5, 1)


@pytest.mark.parametrize("nota", [0, 7.5, 10])
def test_review_schema_accepts_full_scale(nota: float) -> None:
    assert ReviewCreate(nome="X", nota=nota, comentario="Y").nota == nota


@pytest.mark.parametrize("nota", [-0.5, 10.5, 11])
def test_review_schema_rejects_out_of_scale(nota: float) -> None:
    with pytest.raises(ValidationError):
        ReviewCreate(nome="X", nota=nota, comentario="Y")


async def test_list_reviews_paginates_and_checks_movie(
    session: AsyncSession, seeded: dict[str, str]
) -> None:
    page = await review_crud.list_reviews(session, seeded["rings"], PageParams(size=1))

    assert (page.total, page.pages, len(page.items)) == (2, 2, 1)
    with pytest.raises(NotFoundError):
        await review_crud.list_reviews(session, "nope", PageParams())
