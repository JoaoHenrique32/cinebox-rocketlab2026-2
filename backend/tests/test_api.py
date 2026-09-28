"""Testes de integração da API REST (HTTP -> CRUD -> SQLite em memória)."""

from collections.abc import AsyncIterator

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.main import app

API = "/api/v1"


@pytest.fixture
async def client(session: AsyncSession, seeded: dict[str, str]) -> AsyncIterator[httpx.AsyncClient]:
    async def _override_db() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_db] = _override_db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
    app.dependency_overrides.clear()


async def test_list_movies_with_query_params(client: httpx.AsyncClient) -> None:
    response = await client.get(f"{API}/movies", params={"q": "ring", "page": 1, "size": 10})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["titulo"] == "Rings"
    assert body["items"][0]["avaliacao"] == {"nota_media": 7.0, "total_avaliacoes": 2}


@pytest.mark.parametrize(
    "params", [{"size": 0}, {"size": 101}, {"page": 0}, {"ordenar": "aleatorio"}]
)
async def test_list_movies_rejects_invalid_query(
    client: httpx.AsyncClient, params: dict[str, object]
) -> None:
    response = await client.get(f"{API}/movies", params=params)

    assert response.status_code == 422


async def test_movie_lifecycle(client: httpx.AsyncClient) -> None:
    created = await client.post(
        f"{API}/movies",
        json={"titulo": "Novo", "ano_lancamento": 2024, "genero_ids": ["g-drama"]},
    )
    assert created.status_code == 201
    movie_id = created.json()["id"]

    patched = await client.patch(f"{API}/movies/{movie_id}", json={"diretores": ["Fulana"]})
    assert patched.status_code == 200
    assert patched.json()["titulo"] == "Novo"
    assert [d["nome"] for d in patched.json()["diretores"]] == ["Fulana"]

    assert (await client.delete(f"{API}/movies/{movie_id}")).status_code == 204
    assert (await client.get(f"{API}/movies/{movie_id}")).status_code == 404


async def test_domain_errors_are_translated(client: httpx.AsyncClient) -> None:
    missing = await client.get(f"{API}/movies/nope")
    bad_genre = await client.post(f"{API}/movies", json={"titulo": "X", "genero_ids": ["g-x"]})
    null_title = await client.patch(f"{API}/movies/m-rings", json={"titulo": None})

    assert missing.status_code == 404
    assert missing.json() == {"detail": "Filme nope não encontrado"}
    assert bad_genre.status_code == 422
    assert "g-x" in bad_genre.json()["detail"]
    assert null_title.status_code == 422


async def test_reviews_flow_updates_average(
    client: httpx.AsyncClient, seeded: dict[str, str]
) -> None:
    url = f"{API}/movies/{seeded['rings']}/reviews"

    created = await client.post(url, json={"nome": "Admin", "nota": 10, "comentario": "Top"})
    invalid = await client.post(url, json={"nome": "Admin", "nota": 11, "comentario": "X"})
    listing = await client.get(url, params={"size": 10})
    detail = await client.get(f"{API}/movies/{seeded['rings']}")

    assert created.status_code == 201
    assert created.json()["nota"] == 10
    assert invalid.status_code == 422
    assert listing.json()["total"] == 3
    # (8 + 6 + 10) / 3 = 8.0
    assert detail.json()["avaliacao"] == {"nota_media": 8.0, "total_avaliacoes": 3}


async def test_reviews_of_unknown_movie_return_404(client: httpx.AsyncClient) -> None:
    response = await client.post(
        f"{API}/movies/nope/reviews", json={"nome": "A", "nota": 3, "comentario": "B"}
    )

    assert response.status_code == 404


async def test_list_genres(client: httpx.AsyncClient) -> None:
    response = await client.get(f"{API}/genres")

    assert response.status_code == 200
    assert [g["nome"] for g in response.json()] == ["Drama", "Horror"]
