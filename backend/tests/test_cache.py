"""Testes do cache em memória do catálogo."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import cache as cache_module
from app.core.cache import TTLCache
from app.movies.crud import movie as movie_crud
from app.movies.crud import review as review_crud
from app.movies.models import DimMovie, FactMoviePerformance
from app.movies.schemas import MovieFilters, PageParams, ReviewCreate


def test_ttl_cache_expires_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    now = 1000.0
    monkeypatch.setattr(cache_module.time, "monotonic", lambda: now)
    cache: TTLCache[str] = TTLCache(ttl_seconds=60)

    cache.set("k", "v")
    assert cache.get("k") == "v"

    now += 61
    assert cache.get("k") is None
    assert len(cache) == 0


def test_ttl_cache_evicts_oldest_when_full() -> None:
    cache: TTLCache[int] = TTLCache(ttl_seconds=60, max_entries=2)

    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)

    assert cache.get("a") is None
    assert (cache.get("b"), cache.get("c")) == (2, 3)


async def test_catalog_is_served_from_cache_until_a_write(
    session: AsyncSession, seeded: dict[str, str]
) -> None:
    filters, params = MovieFilters(), PageParams()
    first = await movie_crud.list_movies(session, filters, params)

    # Inserção direta (fora do CRUD) não invalida: a página em cache é reaproveitada.
    session.add(
        DimMovie(
            sk_movie_id="m-new",
            id_filme="99",
            titulo="Novo",
            performance=FactMoviePerformance(popularidade=1.0),
        )
    )
    await session.commit()
    cached = await movie_crud.list_movies(session, filters, params)
    assert cached is first

    # Escrita pelo CRUD (nova avaliação) invalida o cache.
    await review_crud.create_review(
        session, seeded["percent"], ReviewCreate(nome="A", nota=5, comentario="B")
    )
    fresh = await movie_crud.list_movies(session, filters, params)
    assert fresh is not first
    assert fresh.total == first.total + 1
