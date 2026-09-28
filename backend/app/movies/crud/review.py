"""Operações de persistência de avaliações individuais."""

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.movies.crud.cache import invalidate_catalog
from app.movies.models import DimMovie, MovieReview
from app.movies.schemas import Page, PageParams, RatingSummary, ReviewCreate, ReviewRead


def to_review_read(review: MovieReview) -> ReviewRead:
    return ReviewRead(
        id=review.sk_movie_review_id,
        nome=review.nome,
        nota=review.nota,
        comentario=review.comentario,
        created_at=review.created_at,
    )


def to_rating_summary(average: float | None, total: int | None) -> RatingSummary:
    return RatingSummary(
        nota_media=round(average, 2) if average is not None else None,
        total_avaliacoes=total or 0,
    )


async def ensure_movie_exists(session: AsyncSession, movie_id: str) -> None:
    exists = await session.scalar(
        select(DimMovie.sk_movie_id).where(DimMovie.sk_movie_id == movie_id)
    )
    if exists is None:
        raise NotFoundError(f"Filme {movie_id} não encontrado")


async def get_rating_summary(session: AsyncSession, movie_id: str) -> RatingSummary:
    """Média calculada sobre ``movie_reviews`` (fonte da verdade, sempre atual)."""

    average, total = (
        await session.execute(
            select(func.avg(MovieReview.nota), func.count()).where(
                MovieReview.sk_movie_id == movie_id
            )
        )
    ).one()
    return to_rating_summary(average, total)


async def get_rating_summaries(
    session: AsyncSession, movie_ids: Sequence[str]
) -> dict[str, RatingSummary]:
    """Resumo de avaliações de vários filmes em uma única consulta agregada."""

    rows = await session.execute(
        select(MovieReview.sk_movie_id, func.avg(MovieReview.nota), func.count())
        .where(MovieReview.sk_movie_id.in_(movie_ids))
        .group_by(MovieReview.sk_movie_id)
    )
    found = {movie_id: to_rating_summary(avg, total) for movie_id, avg, total in rows}
    return {movie_id: found.get(movie_id, to_rating_summary(None, 0)) for movie_id in movie_ids}


async def list_reviews(
    session: AsyncSession, movie_id: str, params: PageParams
) -> Page[ReviewRead]:
    """Avaliações de um filme, das mais recentes para as mais antigas."""

    await ensure_movie_exists(session, movie_id)

    total = await session.scalar(select(func.count()).where(MovieReview.sk_movie_id == movie_id))
    reviews = await session.scalars(
        select(MovieReview)
        .where(MovieReview.sk_movie_id == movie_id)
        .order_by(MovieReview.created_at.desc(), MovieReview.sk_movie_review_id)
        .offset(params.offset)
        .limit(params.size)
    )
    return Page[ReviewRead].build([to_review_read(r) for r in reviews], total or 0, params)


async def create_review(session: AsyncSession, movie_id: str, data: ReviewCreate) -> ReviewRead:
    await ensure_movie_exists(session, movie_id)

    review = MovieReview(
        sk_movie_id=movie_id,
        nome=data.nome,
        nota=data.nota,
        comentario=data.comentario,
    )
    session.add(review)
    await session.commit()
    invalidate_catalog()  # a média do filme mudou
    await session.refresh(review)  # carrega created_at (server_default)
    return to_review_read(review)
