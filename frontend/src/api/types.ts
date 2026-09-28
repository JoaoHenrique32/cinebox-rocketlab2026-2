// Tipos que espelham os schemas do backend (backend/app/movies/schemas).
// Se mudar algo lá, precisa mudar aqui também.

export interface Page<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

export interface Genre {
  id: string
  nome: string
}

export interface Company {
  id: string
  nome: string
}

export interface Person {
  id: string
  nome: string
  tipo: 'Ator' | 'Diretor' | 'Roteirista'
}

// Valores monetários chegam como string (Decimal no Python)
export interface Performance {
  orcamento_usd: string | null
  receita_usd: string | null
  lucro_usd: string
  popularidade: number | null
  nota_tmdb: number | null
  qtd_tmdb: number | null
  nota_imdb: number | null
  qtd_imdb: number | null
}

// Notas sempre de 0 a 10 (mesma escala do banco)
export interface RatingSummary {
  nota_media: number | null // null quando o filme ainda não tem avaliações
  total_avaliacoes: number
}

export interface Review {
  id: string
  nome: string
  nota: number
  comentario: string
  created_at: string
}

export interface ReviewCreate {
  nome: string
  nota: number
  comentario: string
}

export const MOVIE_STATUSES = ['Lançado', 'Em Produção', 'Pós-Produção', 'Planejado'] as const
export type MovieStatus = (typeof MOVIE_STATUSES)[number]

export interface MovieSummary {
  id: string
  titulo: string
  ano_lancamento: number | null
  url_poster: string | null
  generos: Genre[]
  avaliacao: RatingSummary
}

export interface MovieDetail extends MovieSummary {
  data_lancamento: string | null
  duracao_minutos: number | null
  status_filme: string | null
  sinopse: string | null
  url_backdrop: string | null
  diretores: Person[]
  roteiristas: Person[]
  elenco: Person[]
  produtoras: Company[]
  desempenho: Performance | null
}

// Corpo enviado no POST (cadastro) e no PATCH (edição)
export interface MovieInput {
  titulo: string
  data_lancamento: string | null
  ano_lancamento: number | null
  duracao_minutos: number | null
  status_filme: MovieStatus | null
  sinopse: string | null
  url_poster: string | null
  url_backdrop: string | null
  genero_ids: string[]
  diretores: string[]
}

export const SORT_OPTIONS = {
  populares: 'Populares',
  recentes: 'Lançamentos',
  titulo: 'Título (A-Z)',
  melhor_avaliados: 'Melhor avaliados',
} as const
export type MovieSort = keyof typeof SORT_OPTIONS

export interface MovieFilters {
  q?: string
  genero_id?: string
  ano?: number
  ordenar?: MovieSort
  page?: number
  size?: number
}

// Formato dos erros do FastAPI: texto simples ou lista de erros de validação
export interface ApiError {
  detail: string | { loc: (string | number)[]; msg: string }[]
}
