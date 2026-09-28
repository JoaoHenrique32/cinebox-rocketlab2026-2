"""Testes do seed (``scripts/seed.py``).

Os testes principais rodam o seed de verdade sobre uma amostra pequena dos CSVs
(``tests/fixtures/seed_data``) em um SQLite temporário, sem depender dos ~220 MB
de dados da atividade. O último teste confere o banco real e é pulado quando
ele ainda não foi populado.
"""

import csv
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.movies.models import DimGenre, DimMovie, FactMoviePerformance, MovieReview
from scripts.seed import DATA_DIR, build_sync_engine, seed_database

FIXTURE_DATA = Path(__file__).parent / "fixtures" / "seed_data"


@pytest.fixture
def engine(tmp_path: Path) -> Iterator[Engine]:
    engine = build_sync_engine(f"sqlite:///{tmp_path / 'seed.db'}")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


def count(session: Session, model: type[Base]) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0


def test_seed_populates_movies_and_genres(engine: Engine) -> None:
    report = seed_database(engine, FIXTURE_DATA)

    assert report.loaded
    assert report.row_counts["dim_movies"] == 3
    assert report.row_counts["dim_genres"] == 2

    with Session(engine) as session:
        assert count(session, DimMovie) == 3
        genres = session.scalars(select(DimGenre.nome_genero).order_by(DimGenre.nome_genero))
        assert list(genres) == ["Drama", "Horror"]

        # As bridges foram carregadas e o relacionamento N:N funciona pelo ORM.
        rings = session.get(DimMovie, "m-rings")
        assert rings is not None
        assert {g.nome_genero for g in rings.genres} == {"Horror", "Drama"}
        assert rings.performance is not None and rings.performance.qtd_tmdb == 2375
        assert count(session, MovieReview) == 2


def test_seed_cleans_and_converts_values(engine: Engine) -> None:
    seed_database(engine, FIXTURE_DATA)

    with Session(engine) as session:
        blessed = session.get(DimMovie, "m-blessed")
        rings = session.get(DimMovie, "m-rings")
        no_poster = session.get(DimMovie, "m-sem-poster")
        assert blessed is not None and rings is not None and no_poster is not None

        # Escape duplo de aspas do CSV original é desfeito.
        assert blessed.titulo == '"blessed"'
        assert rings.sinopse == 'Julia fica preocupada com o "filme dentro do filme".'
        # Campos vazios viram NULL.
        assert no_poster.url_poster is None
        assert no_poster.sinopse is None


def test_seed_keeps_referential_integrity(engine: Engine) -> None:
    seed_database(engine, FIXTURE_DATA)

    with engine.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []
    with Session(engine) as session:
        # Invariante do esquema estrela: todo filme tem uma linha no fato.
        assert count(session, FactMoviePerformance) == count(session, DimMovie)


def test_seed_is_idempotent_and_reset_reloads(engine: Engine) -> None:
    first = seed_database(engine, FIXTURE_DATA)
    second = seed_database(engine, FIXTURE_DATA)
    assert not second.loaded
    assert second.row_counts == first.row_counts

    with Session(engine) as session, session.begin():
        session.add(DimGenre(nome_genero="Extra"))
    reset = seed_database(engine, FIXTURE_DATA, reset=True)
    assert reset.loaded
    assert reset.row_counts == first.row_counts


def test_seed_fails_clearly_without_csvs(engine: Engine, tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="dim_movies.csv"):
        seed_database(engine, tmp_path / "vazio")

    with Session(engine) as session:
        assert count(session, DimMovie) == 0


# --------------------------------------------------------------------------- #
# Banco real (backend/rocketlab.db)
# --------------------------------------------------------------------------- #
def _real_database_movie_count() -> int:
    engine = build_sync_engine()
    # Não conecta se o arquivo não existe: o SQLite criaria um banco vazio.
    if engine.url.database and not Path(engine.url.database).exists():
        engine.dispose()
        return 0
    try:
        with Session(engine) as session:
            return count(session, DimMovie)
    except Exception:  # banco inexistente ou sem migrações
        return 0
    finally:
        engine.dispose()


GENRES_CSV = DATA_DIR / "bases_atv_dev1" / "dim_genres.csv"


@pytest.mark.skipif(
    not GENRES_CSV.exists() or _real_database_movie_count() == 0,
    reason="banco real ainda não populado: rode `python -m scripts.seed`",
)
def test_real_database_is_seeded() -> None:
    with GENRES_CSV.open(encoding="utf-8", newline="") as file:
        expected_genres = {row["nome_genero"] for row in csv.DictReader(file)}

    engine = build_sync_engine()
    try:
        with Session(engine) as session:
            assert count(session, DimMovie) > 0
            assert set(session.scalars(select(DimGenre.nome_genero))) == expected_genres
            assert count(session, FactMoviePerformance) == count(session, DimMovie)
    finally:
        engine.dispose()
