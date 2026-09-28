"""Carga inicial dos CSVs da camada Diamond no banco criado pelo Alembic.

Uso (a partir de ``backend/``):

    python -m scripts.load_csv            # falha se o banco já tiver dados
    python -m scripts.load_csv --reset    # limpa as tabelas e recarrega tudo

Decisões de projeto:

- Engine **síncrona**: carga em lote é CPU/IO-bound e sequencial; async não traz
  ganho aqui e só complicaria o fluxo. A URL é derivada da mesma ``DATABASE_URL``
  da API, trocando apenas o driver (``aiosqlite`` -> ``pysqlite``).
- **Bulk insert via ``session.execute(insert(Model), rows)``**: com ~1,6M linhas,
  instanciar um objeto ORM por linha seria ordens de grandeza mais lento. O
  manuseio de relacionamentos via ORM continua sendo a regra na camada ``crud/``.
- **Uma única transação**: ou o banco fica completamente populado, ou nada é
  gravado. As tabelas são carregadas em ordem topológica das chaves estrangeiras
  (dimensões -> fato/bridges -> avaliações), com ``PRAGMA foreign_keys=ON``.
- As notas de ``movies_reviews.csv`` já estão na escala 0-10, a mesma usada
  pela API e pelo frontend: nenhuma conversão é necessária.
"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from itertools import islice
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, Table, create_engine, delete, event, func, insert, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import Base
from app.movies.models import (
    DimCompany,
    DimGenre,
    DimMovie,
    DimPerson,
    DimReview,
    FactMoviePerformance,
    MovieReview,
    bridge_movie_company,
    bridge_movie_genre,
    bridge_movie_person,
)

logger = logging.getLogger("load_csv")

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"
DIMENSIONS_DIR = DATA_DIR / "bases_atv_dev1"
FACTS_DIR = DATA_DIR / "bases_atv_dev_2"
BATCH_SIZE = 5_000

Row = dict[str, str]
Record = dict[str, Any]
Target = type[Base] | Table


# --------------------------------------------------------------------------- #
# Conversores: CSV entrega tudo como str; campos vazios viram NULL.
# --------------------------------------------------------------------------- #
def _optional(value: str) -> str | None:
    value = value.strip()
    return value or None


def to_str(value: str) -> str | None:
    return _optional(value)


def to_int(value: str) -> int | None:
    # Contagens exportadas por Pandas chegam como float ("2375.0").
    raw = _optional(value)
    return int(float(raw)) if raw is not None else None


def to_float(value: str) -> float | None:
    raw = _optional(value)
    return float(raw) if raw is not None else None


def to_decimal(value: str) -> Decimal | None:
    raw = _optional(value)
    return Decimal(raw) if raw is not None else None


def to_date(value: str) -> date | None:
    raw = _optional(value)
    return date.fromisoformat(raw) if raw is not None else None


def clean_text(value: str) -> str | None:
    """Desfaz o escape duplo de aspas presente em parte dos títulos e sinopses.

    Algumas linhas foram exportadas já entre aspas e escapadas uma segunda vez,
    resultando em ``"texto com ""aspas"" internas"`` após o parse do CSV. Parte
    delas também foi truncada, perdendo a aspa de fechamento.

    Remove só o par externo (aspas legítimas nas pontas são preservadas:
    ``\"\"\"blessed\"\"\"`` -> ``"blessed"``): a aspa final é externa quando a
    sequência de aspas no fim do texto tem tamanho ímpar.
    """
    raw = _optional(value)
    if raw is None or not raw.startswith('"'):
        return raw
    raw = raw[1:]
    trailing_quotes = len(raw) - len(raw.rstrip('"'))
    if trailing_quotes % 2 == 1:
        raw = raw[:-1]
    return raw.replace('""', '"') or None


def columns(**converters: Callable[[str], Any]) -> Callable[[Row], Record]:
    """Cria um transformador de linha a partir de ``coluna=conversor``."""

    def transform(row: Row) -> Record:
        return {name: convert(row[name]) for name, convert in converters.items()}

    return transform


# --------------------------------------------------------------------------- #
# Plano de carga (ordem = ordem topológica das FKs).
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class CsvSource:
    path: Path
    target: Target
    transform: Callable[[Row], Record]

    @property
    def table(self) -> Table:
        return self.target if isinstance(self.target, Table) else self.target.__table__


LOAD_PLAN: tuple[CsvSource, ...] = (
    # Dimensões independentes
    CsvSource(
        DIMENSIONS_DIR / "dim_movies.csv",
        DimMovie,
        columns(
            sk_movie_id=str,
            id_filme=str,
            titulo=clean_text,
            data_lancamento=to_date,
            ano_lancamento=to_int,
            duracao_minutos=to_int,
            status_filme=to_str,
            sinopse=clean_text,
            url_poster=to_str,
            url_backdrop=to_str,
        ),
    ),
    CsvSource(
        DIMENSIONS_DIR / "dim_genres.csv",
        DimGenre,
        columns(sk_genre_id=str, nome_genero=str),
    ),
    CsvSource(
        DIMENSIONS_DIR / "dim_companies.csv",
        DimCompany,
        columns(sk_company_id=str, nome_produtora=str),
    ),
    CsvSource(
        DIMENSIONS_DIR / "dim_people.csv",
        DimPerson,
        columns(sk_person_id=str, nome_pessoa=str, tipo_pessoa=str),
    ),
    # Dependentes de dim_movies (e das demais dimensões, no caso das bridges)
    CsvSource(
        DIMENSIONS_DIR / "dim_reviews.csv",
        DimReview,
        columns(
            sk_review_id=str,
            sk_movie_id=str,
            qtd_avaliacoes_usuarios=to_int,
            nota_media_usuarios=to_float,
        ),
    ),
    CsvSource(
        FACTS_DIR / "fact_movies_performance.csv",
        FactMoviePerformance,
        columns(
            sk_movie_id=str,
            orcamento_usd=to_decimal,
            receita_usd=to_decimal,
            lucro_usd=to_decimal,
            orcamento_brl=to_decimal,
            receita_brl=to_decimal,
            lucro_brl=to_decimal,
            popularidade=to_float,
            nota_tmdb=to_float,
            qtd_tmdb=to_int,
            nota_imdb=to_float,
            qtd_imdb=to_int,
        ),
    ),
    CsvSource(
        FACTS_DIR / "bridge_movie_genre.csv",
        bridge_movie_genre,
        columns(sk_movie_id=str, sk_genre_id=str),
    ),
    CsvSource(
        FACTS_DIR / "bridge_movie_company.csv",
        bridge_movie_company,
        columns(sk_movie_id=str, sk_company_id=str),
    ),
    CsvSource(
        FACTS_DIR / "bridge_movie_person.csv",
        bridge_movie_person,
        columns(sk_movie_id=str, sk_person_id=str),
    ),
    CsvSource(
        FACTS_DIR / "movies_reviews.csv",
        MovieReview,
        columns(
            sk_movie_review_id=str,
            sk_movie_id=str,
            nome=str,
            nota=float,
            comentario=str,
        ),
    ),
)


# --------------------------------------------------------------------------- #
# Infraestrutura
# --------------------------------------------------------------------------- #
def build_sync_engine() -> Engine:
    """Engine síncrona apontando para o mesmo banco configurado para a API."""

    url = make_url(get_settings().database_url)
    sync_url = url.set(drivername=url.get_backend_name())  # sqlite+aiosqlite -> sqlite
    if sync_url.database and not Path(sync_url.database).is_absolute():
        # Resolve relativo a backend/, independente do diretório de execução.
        sync_url = sync_url.set(database=str(BACKEND_DIR / sync_url.database))

    engine = create_engine(sync_url)

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection: Any, _: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def read_csv(path: Path) -> Iterator[Row]:
    with path.open(encoding="utf-8", newline="") as file:
        yield from csv.DictReader(file)


def batched(rows: Iterator[Record], size: int) -> Iterator[list[Record]]:
    while batch := list(islice(rows, size)):
        yield batch


def count_rows(session: Session, table: Table) -> int:
    return session.scalar(select(func.count()).select_from(table)) or 0


# --------------------------------------------------------------------------- #
# Casos de uso
# --------------------------------------------------------------------------- #
def reset_tables(session: Session) -> None:
    """Esvazia as tabelas em ordem reversa das FKs."""

    for source in reversed(LOAD_PLAN):
        session.execute(delete(source.table))
    logger.info("Tabelas esvaziadas.")


def load_source(session: Session, source: CsvSource) -> int:
    started = time.perf_counter()
    records = (source.transform(row) for row in read_csv(source.path))
    total = 0
    for batch in batched(records, BATCH_SIZE):
        session.execute(insert(source.target), batch)
        total += len(batch)

    logger.info(
        "%-26s %9d linhas  (%.1fs)",
        source.table.name,
        total,
        time.perf_counter() - started,
    )
    return total


def run(*, reset: bool) -> None:
    missing = [str(s.path) for s in LOAD_PLAN if not s.path.exists()]
    if missing:
        raise FileNotFoundError("CSVs ausentes:\n  " + "\n  ".join(missing))

    engine = build_sync_engine()
    started = time.perf_counter()
    try:
        with Session(engine) as session, session.begin():
            if reset:
                reset_tables(session)
            elif count_rows(session, DimMovie.__table__):
                raise RuntimeError("O banco já contém filmes. Use --reset para recarregar do zero.")

            for source in LOAD_PLAN:
                load_source(session, source)

        # Atualiza as estatísticas do otimizador de consultas após a carga em massa.
        with engine.connect() as connection:
            connection.exec_driver_sql("ANALYZE")
        # session.begin() faz commit ao sair sem exceção e rollback caso contrário.
    finally:
        engine.dispose()

    logger.info("Carga concluída em %.1fs.", time.perf_counter() - started)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--reset",
        action="store_true",
        help="apaga os dados existentes antes de carregar",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
    csv.field_size_limit(sys.maxsize if sys.maxsize < 2**31 else 2**31 - 1)

    try:
        run(reset=args.reset)
    except (FileNotFoundError, RuntimeError) as exc:
        logger.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
