"""Fixtures compartilhadas: banco SQLite em memória isolado por teste."""

from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import enable_sqlite_foreign_keys
from app.movies.crud.cache import invalidate_catalog
from app.movies.models import (
    DimGenre,
    DimMovie,
    DimPerson,
    FactMoviePerformance,
    MovieReview,
)


@pytest.fixture(autouse=True)
def _clear_catalog_cache() -> None:
    """O cache é global ao processo: cada teste começa sem resultados guardados."""

    invalidate_catalog()


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    enable_sqlite_foreign_keys(engine)
    async with engine.begin() as conn:
        # Nos testes o schema vem do metadata; em produção, exclusivamente do Alembic.
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    async with factory() as db:
        yield db
    await engine.dispose()


@pytest.fixture
async def seeded(session: AsyncSession) -> dict[str, str]:
    """Catálogo mínimo: 3 filmes, 2 gêneros, 1 diretor, 3 avaliações."""

    drama = DimGenre(sk_genre_id="g-drama", nome_genero="Drama")
    horror = DimGenre(sk_genre_id="g-horror", nome_genero="Horror")
    director = DimPerson(sk_person_id="p-dir", nome_pessoa="Ana Diretora", tipo_pessoa="Diretor")
    actor = DimPerson(sk_person_id="p-act", nome_pessoa="Beto Ator", tipo_pessoa="Ator")

    rings = DimMovie(
        sk_movie_id="m-rings",
        id_filme="1",
        titulo="Rings",
        ano_lancamento=2017,
        genres=[horror],
        people=[director, actor],
        performance=FactMoviePerformance(popularidade=10.0),
        reviews=[
            MovieReview(nome="A", nota=8.0, comentario="Bom"),
            MovieReview(nome="B", nota=6.0, comentario="Ok"),
        ],
    )
    mixtape = DimMovie(
        sk_movie_id="m-mixtape",
        id_filme="2",
        titulo="Mixtape",
        ano_lancamento=2021,
        genres=[drama],
        performance=FactMoviePerformance(popularidade=50.0),
        reviews=[MovieReview(nome="C", nota=10.0, comentario="Perfeito")],
    )
    percent = DimMovie(
        sk_movie_id="m-percent",
        id_filme="3",
        titulo="100% Wolf",
        genres=[drama],
        performance=FactMoviePerformance(popularidade=None),
    )

    session.add_all([rings, mixtape, percent])
    await session.commit()
    return {"rings": "m-rings", "mixtape": "m-mixtape", "percent": "m-percent"}
