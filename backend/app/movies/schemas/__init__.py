"""DTOs Pydantic do domínio de filmes."""

from app.movies.schemas.common import Page, PageParams
from app.movies.schemas.movie import (
    CompanyRead,
    GenreRead,
    MovieCreate,
    MovieDetail,
    MovieFilters,
    MovieListQuery,
    MovieSort,
    MovieSummary,
    MovieUpdate,
    PerformanceRead,
    PersonRead,
)
from app.movies.schemas.review import RatingSummary, ReviewCreate, ReviewRead

__all__ = [
    "CompanyRead",
    "GenreRead",
    "MovieCreate",
    "MovieDetail",
    "MovieFilters",
    "MovieListQuery",
    "MovieSort",
    "MovieSummary",
    "MovieUpdate",
    "Page",
    "PageParams",
    "PerformanceRead",
    "PersonRead",
    "RatingSummary",
    "ReviewCreate",
    "ReviewRead",
]
