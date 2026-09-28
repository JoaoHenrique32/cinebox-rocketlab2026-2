# Cinebox

Sistema de avaliação de filmes desenvolvido para a atividade do RocketLab 2026.2.
O administrador navega por um catálogo com mais de 95 mil filmes, vê os detalhes e
o histórico de avaliações de cada um, gerencia o catálogo (cadastrar, editar,
remover) e adiciona notas e resenhas.

> **O design e a paleta de cores foram fortemente inspirados no
> [Letterboxd](https://letterboxd.com/)**: tema escuro em tons de azul-ardósia com
> os acentos verde, laranja e azul característicos da plataforma.

## Funcionalidades

**Requisitos da atividade**

- Cadastro de filmes (título, diretor(es), data/ano de lançamento, gêneros, sinopse, duração, status, pôster)
- Catálogo paginado com todos os filmes
- Página de detalhes com informações completas (elenco, roteiro, produtoras, bilheteria) e lista de avaliações
- Busca por título
- Edição e remoção de filmes
- Nova avaliação com **nota de 0 a 10** e resenha em texto
- Média geral das avaliações de cada filme

**Extras**

- Filtros por gênero e ano e ordenação (populares, lançamentos, título, melhor avaliados)
- **Cache em memória** das consultas do catálogo no backend, invalidado a cada escrita
- **Testes automatizados** no backend (pytest) e no frontend (Vitest + Testing Library)
- **Layout responsivo**: a grade vai de 2 colunas no celular a 6 no desktop
- Filtros e página salvos na URL (links compartilháveis, botão "voltar" funciona)
- Índices no banco para ordenar e agregar notas rapidamente

> **Escala de notas:** seguindo a orientação oficial da atividade, as avaliações
> usam a escala **0 a 10** definida nas models, e não 0 a 5 como no documento.

## Tecnologias

| Camada | Stack |
|---|---|
| Frontend | Vite, React 19, TypeScript, Tailwind CSS 4, Axios, React Router |
| Backend | FastAPI, SQLAlchemy 2 (async), Pydantic 2, Alembic |
| Banco | SQLite |
| Testes | pytest + httpx (backend), Vitest + Testing Library (frontend) |

## Como executar

### Pré-requisitos

- Python 3.11 ou superior
- Node.js 20 ou superior
- Os arquivos CSV da atividade (não versionados por causa do tamanho, ~220 MB)

### 1. Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -e ".[dev]"
cp .env.example .env          # no Windows (cmd): copy .env.example .env
alembic upgrade head          # cria as tabelas
```

### 2. Carga dos dados

Coloque os CSVs em `backend/data/`, mantendo as duas pastas originais:

```text
backend/data/
├── bases_atv_dev1/     dim_movies, dim_genres, dim_companies, dim_people, dim_reviews
└── bases_atv_dev_2/    bridge_movie_*, fact_movies_performance, movies_reviews
```

Depois, ainda na pasta `backend` com o ambiente virtual ativo:

```bash
python -m scripts.load_csv            # leva alguns minutos (~1,6 milhão de linhas)
python -m scripts.load_csv --reset    # para apagar tudo e carregar de novo
```

### 3. Subir a API

```bash
uvicorn app.main:app --reload
```

A API fica em `http://localhost:8000`, com documentação interativa em
`http://localhost:8000/docs`.

> Com `ENVIRONMENT=local` no `.env`, o SQLAlchemy imprime todas as consultas SQL
> no terminal. Para um log mais limpo, use `ENVIRONMENT=dev`.

### 4. Frontend

Em outro terminal:

```bash
cd frontend
npm install
cp .env.example .env          # opcional: a URL padrão já é http://localhost:8000/api/v1
npm run dev
```

Acesse `http://localhost:5173`.

## Testes

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

## Endpoints principais

Todos com o prefixo `/api/v1`:

| Método | Rota | Descrição |
|---|---|---|
| GET | `/movies?q=&genero_id=&ano=&ordenar=&page=&size=` | Catálogo paginado com busca e filtros |
| POST | `/movies` | Cadastra um filme |
| GET | `/movies/{id}` | Detalhes do filme com a média das avaliações |
| PATCH | `/movies/{id}` | Atualiza campos do filme |
| DELETE | `/movies/{id}` | Remove o filme e suas avaliações |
| GET | `/movies/{id}/reviews?page=&size=` | Avaliações do filme |
| POST | `/movies/{id}/reviews` | Adiciona uma avaliação (nota de 0 a 10) |
| GET | `/genres` | Lista de gêneros |

## Estrutura

```text
.
├── backend/
│   ├── app/
│   │   ├── api/            rotas HTTP e tratamento de erros
│   │   ├── core/           configurações, exceções e cache
│   │   ├── db/             engine e sessões do SQLAlchemy
│   │   └── movies/
│   │       ├── models.py   modelo ORM (esquema estrela)
│   │       ├── schemas/    DTOs Pydantic
│   │       └── crud/       regras de negócio e consultas
│   ├── migrations/         Alembic
│   ├── scripts/            carga dos CSVs
│   ├── tests/
│   └── ARCHITECTURE.md     decisões de arquitetura do backend
└── frontend/
    └── src/
        ├── api/            cliente Axios e tipos da API
        ├── components/     MovieCard, SearchBar, RatingBadge, ReviewForm...
        ├── pages/          catálogo, detalhes, formulário
        └── utils/          formatação
```

As principais decisões técnicas do backend (camadas, cálculo da média, índices,
cache e carga dos dados) estão documentadas em
[`backend/ARCHITECTURE.md`](backend/ARCHITECTURE.md).
