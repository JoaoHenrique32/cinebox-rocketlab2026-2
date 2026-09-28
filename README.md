<div align="center">

# 🎬 Cinebox

**Catálogo e avaliação de filmes com a experiência visual do Letterboxd**

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy_2-async-D71F00?logo=sqlalchemy&logoColor=white)
![React](https://img.shields.io/badge/React_19-20232A?logo=react&logoColor=61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS_4-06B6D4?logo=tailwindcss&logoColor=white)
![Tests](https://img.shields.io/badge/testes-pytest_%7C_Vitest-6E9F18)

</div>

---

## Sumário

- [Sobre o projeto](#sobre-o-projeto)
- [Destaques técnicos](#destaques-técnicos)
- [Funcionalidades](#funcionalidades)
- [Tecnologias](#tecnologias)
- [Como executar](#como-executar)
- [Testes](#testes)
- [Endpoints da API](#endpoints-da-api)
- [Estrutura do repositório](#estrutura-do-repositório)

---

## Sobre o projeto

O **Cinebox** é um sistema de catálogo e avaliação de filmes desenvolvido para a
atividade do **RocketLab 2026.2**. Um administrador navega por um acervo com
**mais de 95 mil filmes**, consulta detalhes completos (elenco, roteiro,
produtoras, bilheteria), acompanha o histórico de avaliações e gerencia o
catálogo: cadastra, edita, remove e avalia títulos.

### Inspiração visual

A interface foi fortemente inspirada no **[Letterboxd](https://letterboxd.com/)**:
tema escuro em tons de azul-ardósia, pôsteres como protagonistas da grade e os
acentos **verde**, **laranja** e **azul** característicos da plataforma. O
objetivo foi entregar uma experiência familiar para quem já usa redes sociais de
cinema, sem abrir mão da clareza de uma ferramenta administrativa.

---

## Destaques técnicos

| | Melhoria | O que foi feito |
|---|---|---|
| ✅ | **Testes automatizados** | Backend com **pytest + httpx** (models, CRUD, API, cache e seed sobre amostras reais dos CSVs). Frontend com **Vitest + Testing Library** (componentes, página de catálogo e cliente HTTP). |
| ⚡ | **Caching** | Cache em memória com TTL para as páginas do catálogo e para a lista de anos, **invalidado a cada escrita** (filme ou avaliação), além de índices dedicados para ordenação e agregação de notas. |
| 📱 | **Responsividade** | Layout *mobile-first* com Tailwind: a grade vai de **2 colunas no celular a 6 no desktop**, e os filtros se reorganizam conforme a largura da tela. |
| 🗓️ | **Filtros orientados a dados** | O filtro de ano é populado por `GET /movies/years`, que devolve apenas os anos que realmente existem no banco: nada de anos futuros ou opções que levam a buscas vazias. |
| 🔗 | **Estado na URL** | Busca, filtros e página ficam na query string: links compartilháveis e botão "voltar" funcionando. |
| 🧱 | **Arquitetura em camadas** | `models` (ORM) → `schemas` (Pydantic) → `crud` (regras de negócio) → `api` (HTTP). As rotas apenas delegam e traduzem exceções de domínio em status HTTP. |

---

## Funcionalidades

**Requisitos da atividade**

- Cadastro de filmes (título, diretor(es), data/ano de lançamento, gêneros, sinopse, duração, status, pôster)
- Catálogo paginado com todos os filmes
- Página de detalhes com informações completas e lista de avaliações
- Busca por título
- Edição e remoção de filmes
- Nova avaliação com **nota de 0 a 10** e resenha em texto
- Média geral das avaliações de cada filme

**Extras**

- Filtros por gênero e ano e ordenação (populares, lançamentos, título, melhor avaliados)
- Seed oficial do banco a partir dos CSVs da atividade

> [!NOTE]
> **Escala de notas:** seguindo a orientação oficial da atividade, as avaliações
> usam a escala **0 a 10** definida nas models, e não 0 a 5 como no documento.

---

## Tecnologias

| Camada | Stack |
|---|---|
| Frontend | Vite, React 19, TypeScript, Tailwind CSS 4, Axios, React Router |
| Backend | FastAPI, SQLAlchemy 2 (async), Pydantic 2, Alembic |
| Banco | SQLite (esquema estrela com tabelas *bridge* N:N) |
| Testes | pytest + httpx (backend), Vitest + Testing Library (frontend) |

---

## Como executar

### Pré-requisitos

- **Python** 3.11 ou superior
- **Node.js** 20 ou superior
- Os **arquivos CSV** da atividade (não versionados por causa do tamanho, ~220 MB)

### Passo 1 — Preparar o backend

```bash
cd backend
python -m venv .venv
```

Ative o ambiente virtual:

```bash
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate
```

Instale as dependências e crie o arquivo de configuração:

```bash
pip install -e ".[dev]"
cp .env.example .env
```

> No Windows (cmd), use `copy .env.example .env`.

### Passo 2 — Popular o banco (seed)

O seed aplica as migrações do Alembic (cria as tabelas) e carrega os dados da
atividade, para que a aplicação não comece vazia.

**2.1.** Coloque os CSVs em `backend/data/`, mantendo as duas pastas originais:

```text
backend/data/
├── bases_atv_dev1/     dim_movies, dim_genres, dim_companies, dim_people, dim_reviews
└── bases_atv_dev_2/    bridge_movie_*, fact_movies_performance, movies_reviews
```

**2.2.** Ainda na pasta `backend`, com o ambiente virtual ativo, execute:

```bash
python -m scripts.seed
```

A primeira execução leva alguns minutos (~1,6 milhão de linhas) e termina
exibindo quantas linhas cada tabela recebeu.

| Comando | Quando usar |
|---|---|
| `python -m scripts.seed` | Primeira carga. É idempotente: se o banco já estiver populado, nada é alterado. |
| `python -m scripts.seed --reset` | Apaga todos os dados e popula novamente do zero. |

### Passo 3 — Iniciar a API

```bash
uvicorn app.main:app --reload
```

| Recurso | URL |
|---|---|
| API | http://localhost:8000/api/v1 |
| Documentação interativa (Swagger) | http://localhost:8000/docs |

> [!TIP]
> Com `ENVIRONMENT=local` no `.env`, o SQLAlchemy imprime todas as consultas SQL
> no terminal. Para um log mais limpo, use `ENVIRONMENT=dev`.

### Passo 4 — Iniciar o frontend

Em **outro terminal**:

```bash
cd frontend
npm install
cp .env.example .env    # opcional: a URL padrão já é http://localhost:8000/api/v1
npm run dev
```

Acesse **http://localhost:5173**.

---

## Testes

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

No backend, `tests/test_seed.py` roda o seed sobre uma amostra dos CSVs
(`tests/fixtures/seed_data`) e confere se filmes, gêneros e seus relacionamentos
foram populados corretamente. Depois do seed real, o mesmo arquivo também valida
o banco de verdade (antes disso, esse teste aparece como *skipped*).

---

## Endpoints da API

Todos com o prefixo `/api/v1`:

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/movies?q=&genero_id=&ano=&ordenar=&page=&size=` | Catálogo paginado com busca e filtros |
| `GET` | `/movies/years` | Anos de lançamento existentes no banco (mais recentes primeiro) |
| `POST` | `/movies` | Cadastra um filme |
| `GET` | `/movies/{id}` | Detalhes do filme com a média das avaliações |
| `PATCH` | `/movies/{id}` | Atualiza campos do filme |
| `DELETE` | `/movies/{id}` | Remove o filme e suas avaliações |
| `GET` | `/movies/{id}/reviews?page=&size=` | Avaliações do filme |
| `POST` | `/movies/{id}/reviews` | Adiciona uma avaliação (nota de 0 a 10) |
| `GET` | `/genres` | Lista de gêneros |

---

## Estrutura do repositório

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
│   ├── scripts/            seed do banco (seed.py)
│   └── tests/
└── frontend/
    └── src/
        ├── api/            cliente Axios e tipos da API
        ├── components/     MovieCard, SearchBar, RatingBadge, ReviewForm...
        ├── pages/          catálogo, detalhes, formulário
        └── utils/          formatação
```
