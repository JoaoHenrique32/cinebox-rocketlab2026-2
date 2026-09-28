"""Cache das páginas do catálogo (``GET /movies``).

Fica em um módulo próprio porque é invalidado tanto pelo CRUD de filmes
quanto pelo de avaliações (a média aparece nos cards do catálogo).
"""

from app.core.cache import TTLCache
from app.core.config import get_settings
from app.movies.schemas import MovieFilters, MovieSummary, Page, PageParams

catalog_cache: TTLCache[Page[MovieSummary]] = TTLCache(
    ttl_seconds=get_settings().catalog_cache_ttl_seconds
)


def catalog_key(filters: MovieFilters, params: PageParams) -> tuple[object, ...]:
    return (filters.q, filters.genero_id, filters.ano, filters.ordenar, params.page, params.size)


def invalidate_catalog() -> None:
    """Chamado após qualquer escrita que altere o que o catálogo exibe."""

    catalog_cache.clear()
