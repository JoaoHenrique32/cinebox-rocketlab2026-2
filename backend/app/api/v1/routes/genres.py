from fastapi import APIRouter

from app.api.deps import SessionDep
from app.movies.crud import movie as movie_crud
from app.movies.schemas import GenreRead

router = APIRouter()


@router.get("", response_model=list[GenreRead], summary="Lista os gêneros disponíveis")
async def list_genres(session: SessionDep) -> list[GenreRead]:
    return await movie_crud.list_genres(session)
