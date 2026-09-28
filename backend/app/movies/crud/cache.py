"""Cache das páginas do catálogo (``GET /movies``) e dos anos disponíveis.

Fica em um módulo próprio porque é invalidado tanto pelo CRUD de filmes
quanto pelo de avaliações (a média aparece nos cards do catálogo).
"""

from app.core.cache import TTLCache
from app.core.config import get_settings
from app.movies.schemas import MovieFilters, MovieSummary, Page, PageParams

catalog_cache: TTLCache[Page[MovieSummary]] = TTLCache(
    ttl_seconds=get_settings().catalog_cache_ttl_seconds
)

# Uma única entrada: a lista de anos distintos só muda quando um filme é escrito.
years_cache: TTLCache[list[int]] = TTLCache(
    ttl_seconds=get_settings().catalog_cache_ttl_seconds, max_entries=1
)
YEARS_KEY = "years"


def catalog_key(filters: MovieFilters, params: PageParams) -> tuple[object, ...]:
    return (filters.q, filters.genero_id, filters.ano, filters.ordenar, params.page, params.size)


def invalidate_catalog() -> None:
    """Chamado após qualquer escrita que altere o que o catálogo exibe."""

    catalog_cache.clear()
    years_cache.clear()
