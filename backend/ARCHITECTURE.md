# Arquitetura do backend

Registro conciso das decisões estruturais do backend do Cinebox. Cada seção
descreve **o que** foi decidido e **por quê**; o código é a referência do
**como**.

## 1. Camadas

```
api/  ──►  crud/  ──►  models.py (ORM)  ──►  SQLite
 │           │
 └── schemas/ (DTOs Pydantic) ◄──┘
```

| Camada | Local | Responsabilidade |
|---|---|---|
| HTTP | `app/api/v1/` | Roteamento, parâmetros, status codes. Sem regra de negócio. |
| DTOs | `app/movies/schemas/` | Contrato de entrada/saída (Pydantic v2) e validação sintática. |
| Domínio/dados | `app/movies/crud/` | Regras de negócio, consultas e transações. |
| ORM | `app/movies/models.py` | Mapeamento do esquema estrela. |

- **O CRUD devolve DTOs, nunca objetos ORM.** A camada HTTP fica isolada do
  ORM, e o lazy loading (proibido em `AsyncSession`) nunca é acionado fora do
  CRUD, onde todo relacionamento é carregado com `selectinload`.
- **Falhas de regra de negócio viram exceções de domínio**
  (`app/core/exceptions.py`: `NotFoundError`, `InvalidReferenceError`). A
  camada HTTP apenas as traduz em status codes, via exception handlers.
- **O CRUD controla a transação** (`commit`) de cada caso de uso de escrita.

## 2. Escala de notas

- **Tudo em 0–10**: banco (`movie_reviews.nota`), API e frontend. A
  orientação oficial da atividade manda seguir as models (0 a 10) em vez do
  documento (0 a 5).
- Como as escalas coincidem, **não há camada de conversão**: a nota enviada é
  gravada como veio, e as médias são arredondadas para 2 casas no CRUD.
- Entrada (`ReviewCreate.nota`) e saída (`ReviewRead.nota`,
  `RatingSummary.nota_media`) usam o mesmo tipo `Score` (`0 ≤ nota ≤ 10`).

## 3. Média de avaliações

- A média e a contagem são **sempre calculadas em tempo real** a partir de
  `movie_reviews` (`AVG`/`COUNT`).
- **`dim_reviews` não é usada pela API.** O CSV original é inconsistente com
  `movie_reviews` (26.604 resumos contra 40.267 filmes avaliados, com 8.593
  divergências), e uma dimensão estática ficaria desatualizada a cada nova
  avaliação. Ela é carregada apenas para preservar o dataset.

## 4. Catálogo: paginação, busca e ordenação

- Paginação por offset (`PageParams`: `page` ≥ 1, `size` 1–100), com resposta
  envelopada em `Page[T]` (`items`, `total`, `page`, `size`, `pages`).
- A listagem é feita em **três consultas**, nenhuma proporcional ao catálogo
  inteiro quando há índice:
  1. `COUNT` sobre a consulta filtrada;
  2. página de filmes (`LIMIT/OFFSET`) + gêneros via `selectinload`;
  3. médias **apenas dos IDs da página** (`WHERE sk_movie_id IN (...) GROUP BY`).
- Um *outer join* com as médias de todo o catálogo foi medido e descartado:
  custava cerca de 300 ms por requisição.
- **Os JOINs de ordenação são INNER de propósito**, para o SQLite percorrer o
  índice em vez de ordenar 95 mil linhas.
- Toda ordenação termina com desempate pela PK, o que garante paginação estável.
- Ordenações (`MovieSort`): `populares` (padrão), `recentes`, `titulo`,
  `melhor_avaliados`. A última **considera apenas filmes com ao menos uma
  avaliação**.
- Busca: `ILIKE` no título, com `%`, `_` e `\` escapados. Filtros por gênero
  (`EXISTS` na bridge) e por ano.

### Cache em memória (`app/core/cache.py`, `app/movies/crud/cache.py`)

- As páginas de `GET /movies` ficam em um `TTLCache` (60 s por padrão,
  `CATALOG_CACHE_TTL_SECONDS`, até 256 entradas). A chave é a combinação de
  filtros, ordenação e paginação.
- **A invalidação é explícita**: criar, editar ou remover um filme e criar uma
  avaliação limpam o cache, já que a média aparece nos cards. O TTL é só uma
  rede de segurança.
- O cache é por processo, o que basta para um único worker com SQLite. Com
  vários workers, o próximo passo seria um cache compartilhado (Redis).

### Índices adicionados (migração `dccf1d8c36b3`)

| Índice | Uso | Efeito medido |
|---|---|---|
| `fact_movies_performance(popularidade, sk_movie_id)` | ordenação `populares` | 1.110 ms → 68 ms |
| `movie_reviews(sk_movie_id, nota)` | índice de cobertura para `AVG`/`COUNT` | `melhor_avaliados` 412 ms → ~70 ms (SQL puro) |

## 5. Invariantes do esquema estrela

- **Todo filme possui exatamente uma linha em `fact_movies_performance`.**
  A carga garante isso (95.645/95.645), e `create_movie` cria a linha (com
  métricas nulas) junto com o filme. É isso que torna seguro o INNER JOIN da
  ordenação por popularidade.
- No SQLite, `NULL` fica por último em `ORDER BY ... DESC`; por isso não há
  `NULLS LAST` explícito, que impediria o uso do índice.
- Filmes criados pela API recebem `id_filme = "cinebox-<uuid>"`, já que o
  campo identifica o filme na origem (TMDB) e é `UNIQUE`.

## 6. Escrita de filmes

- **Relacionamentos são manipulados via ORM** (`movie.genres = [...]`), nunca
  por inserção direta nas bridges.
- **Gêneros** são referenciados por ID; IDs inexistentes geram
  `InvalidReferenceError`.
- **Diretores** são informados por nome, com *get-or-create* em `dim_people`
  (tipo `Diretor`). Assim a `UNIQUE(nome_pessoa, tipo_pessoa)` é respeitada e
  pessoas existentes são reaproveitadas.
- **Atualização é PATCH**: só os campos enviados (`exclude_unset`) mudam.
  Listas enviadas substituem as atuais, e trocar diretores preserva elenco e
  roteiristas. `null` é rejeitado em campos obrigatórios.
- `ano_lancamento` é derivado de `data_lancamento`; o schema rejeita os dois
  quando divergem.
- **A exclusão é um `DELETE` de Core** e depende de `ON DELETE CASCADE`
  (`PRAGMA foreign_keys=ON` em toda conexão). Bridges, fato e avaliações caem
  junto sem que as coleções sejam carregadas.

## 7. Carga inicial (`scripts/load_csv.py`)

- Engine **síncrona**, derivada da mesma `DATABASE_URL` da API. Async não traz
  ganho numa carga sequencial.
- *Bulk insert* via Core (`session.execute(insert(Model), batch)`), em lotes de
  5.000. Um objeto ORM por linha seria inviável para ~1,6 M linhas.
  A regra "relacionamentos via ORM" vale para o `crud/`, não para o ETL.
- **Uma única transação**, na ordem topológica das FKs: tudo ou nada.
- Recusa rodar sobre um banco já populado (`--reset` para recarregar) e
  executa `ANALYZE` ao final.
- Limpeza de dados: remove o escape duplo de aspas em títulos (55) e sinopses
  (4.801). Nomes de pessoas e produtoras com lixo de parsing upstream são
  mantidos: não são recuperáveis com segurança e colidiriam com as `UNIQUE`.
- Lacuna conhecida do dataset: **20.037 filmes não têm gênero** em
  `bridge_movie_genre.csv`. `generos: []` é um estado válido, e o frontend
  deve tratá-lo.

## 8. API REST (`/api/v1`)

| Método | Rota | Resposta |
|---|---|---|
| GET | `/movies?q&genero_id&ano&ordenar&page&size` | `200 Page[MovieSummary]` |
| POST | `/movies` | `201 MovieDetail` |
| GET | `/movies/{id}` | `200 MovieDetail` |
| PATCH | `/movies/{id}` | `200 MovieDetail` |
| DELETE | `/movies/{id}` | `204` |
| GET | `/movies/{id}/reviews?page&size` | `200 Page[ReviewRead]` |
| POST | `/movies/{id}/reviews` | `201 ReviewRead` |
| GET | `/genres` | `200 list[GenreRead]` |

- As rotas só delegam ao CRUD. A sessão chega por `SessionDep`
  (`app/api/deps.py`).
- Mapeamento de erros (`app/api/errors.py`): `NotFoundError` → **404**;
  `InvalidReferenceError` → **422**, mesmo código da validação do Pydantic;
  outro `DomainError` → 400. O corpo é sempre `{"detail": ...}`.
- A query string do catálogo é um único modelo, `MovieListQuery(MovieFilters,
  PageParams)`, porque o FastAPI aceita só um modelo Pydantic por fonte de
  parâmetros. Por herança, o mesmo objeto satisfaz as duas assinaturas do CRUD.

## 9. Testes

- SQLite em memória (`StaticPool`) com FKs ativas, isolado por teste. O schema
  vem de `Base.metadata.create_all` apenas nos testes; em runtime, só o
  Alembic cria ou altera tabelas.
- `tests/test_crud.py` cobre as regras de domínio: conversão de escala,
  cascade, get-or-create de diretores, PATCH parcial, escape da busca e
  paginação.
- `tests/test_api.py` faz a integração HTTP via `httpx.ASGITransport`,
  sobrescrevendo `get_db`. Cobre status codes, validação de query e payload,
  ciclo de vida do filme e a média atualizada após uma nova avaliação.
