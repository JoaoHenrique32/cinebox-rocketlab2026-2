from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import SessionDep
from app.movies.crud import movie as movie_crud
from app.movies.crud import review as review_crud
from app.movies.schemas import (
    MovieCreate,
    MovieDetail,
    MovieListQuery,
    MovieSummary,
    MovieUpdate,
    Page,
    PageParams,
    ReviewCreate,
    ReviewRead,
)

router = APIRouter()

NOT_FOUND = {status.HTTP_404_NOT_FOUND: {"description": "Filme não encontrado"}}
INVALID_REFERENCE = {
    status.HTTP_422_UNPROCESSABLE_CONTENT: {
        "description": "Payload inválido ou referência a gênero inexistente"
    }
}


# --------------------------------------------------------------------------- #
# Filmes
# --------------------------------------------------------------------------- #
@router.get("", response_model=Page[MovieSummary], summary="Catálogo paginado com busca")
async def list_movies(
    session: SessionDep,
    query: Annotated[MovieListQuery, Query()],
) -> Page[MovieSummary]:
    return await movie_crud.list_movies(session, filters=query, params=query)


@router.post(
    "",
    response_model=MovieDetail,
    status_code=status.HTTP_201_CREATED,
    responses=INVALID_REFERENCE,
    summary="Cadastra um filme",
)
async def create_movie(session: SessionDep, payload: MovieCreate) -> MovieDetail:
    return await movie_crud.create_movie(session, payload)


@router.get(
    "/{movie_id}", response_model=MovieDetail, responses=NOT_FOUND, summary="Detalhes do filme"
)
async def get_movie(session: SessionDep, movie_id: str) -> MovieDetail:
    return await movie_crud.get_movie(session, movie_id)


@router.patch(
    "/{movie_id}",
    response_model=MovieDetail,
    responses={**NOT_FOUND, **INVALID_REFERENCE},
    summary="Atualiza parcialmente um filme",
)
async def update_movie(session: SessionDep, movie_id: str, payload: MovieUpdate) -> MovieDetail:
    return await movie_crud.update_movie(session, movie_id, payload)


@router.delete(
    "/{movie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NOT_FOUND,
    summary="Remove um filme e suas avaliações",
)
async def delete_movie(session: SessionDep, movie_id: str) -> None:
    await movie_crud.delete_movie(session, movie_id)


# --------------------------------------------------------------------------- #
# Avaliações
# --------------------------------------------------------------------------- #
@router.get(
    "/{movie_id}/reviews",
    response_model=Page[ReviewRead],
    responses=NOT_FOUND,
    summary="Avaliações do filme (mais recentes primeiro)",
)
async def list_reviews(
    session: SessionDep, movie_id: str, pagination: Annotated[PageParams, Query()]
) -> Page[ReviewRead]:
    return await review_crud.list_reviews(session, movie_id, pagination)


@router.post(
    "/{movie_id}/reviews",
    response_model=ReviewRead,
    status_code=status.HTTP_201_CREATED,
    responses=NOT_FOUND,
    summary="Adiciona uma avaliação (nota de 0 a 10)",
)
async def create_review(session: SessionDep, movie_id: str, payload: ReviewCreate) -> ReviewRead:
    return await review_crud.create_review(session, movie_id, payload)
